from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from .models import School, Books, Purchase, PurchaseItems, Syllabus, SharedQuestionPaper, OtherDetails, TeacherLog
from datetime import datetime
def home(request): return render(request, 'home.html')
def about(request): return render(request, 'about.html')
def our_story(request): return render(request, 'our_story.html')
def request_demo(request): return render(request, 'request_demo.html')

def school_login(request):
    if request.method == 'POST':
        school_name = request.POST.get('school_name')
        school_id = request.POST.get('school_id')
        password = request.POST.get('password')
        
        school = School.objects.filter(school_name=school_name, school_id=school_id, password_hash=password).first()
        if school:
            teacher_name = request.POST.get('teacher_name')
            # Log the teacher login
            TeacherLog.objects.create(
                teacher_name=teacher_name,
                school_name=school.school_name,
                branch=school.branch
            )
            request.session['school_id'] = school.school_id
            return redirect('school_dashboard')
        else:
            return render(request, 'school_login.html', {'error': 'Invalid credentials. Please check your school name, ID, and password.'})
    return render(request, 'school_login.html')

def student_login(request): return render(request, 'student_login.html')
def contact(request): return render(request, 'contact.html')
def products(request): return render(request, 'products.html')
def school_dashboard(request):
    school_id = request.session.get('school_id')
    if not school_id:
        return redirect('school_login')
            
    school = get_object_or_404(School, pk=school_id)
    purchases = PurchaseItems.objects.filter(purchase__school=school).select_related('book')
    
    from collections import defaultdict
    import datetime
    series_dict = defaultdict(list)
    ebooks = []
    keybooks = []
    purchased_series_set = set()
    
    has_keybook_access = False
    has_qp_access = False

    today = datetime.date.today()

    for p in purchases:
        series_dict[p.book.series_name].append(p.book.class_field)
        purchased_series_set.add(p.book.series_name)
        
        # Check permissions
        if p.keybook_access:
            has_keybook_access = True
        if p.question_paper_access:
            has_qp_access = True
        
        book_path = p.book.path if p.book.path else ''
        if book_path:
            # If the path in the database already starts with '/media/', use it as is
            # otherwise, prepend '/media/' ensuring there are no double slashes
            if book_path.startswith('/media/'):
                view_url = book_path
            else:
                view_url = f"/media/{book_path.lstrip('/')}"
        else:
            view_url = '#'
            
        is_expired = False
        if p.valid_upto and p.valid_upto < today:
            is_expired = True
        
        ebook_data = {
            'title': f"{p.book.series_name} - Class {p.book.class_field}",
            'view_url': view_url,
            'valid_upto': p.valid_upto,
            'is_expired': is_expired
        }
        if p.sent_to_school:
            ebooks.append(ebook_data)
        
        # Add to keybooks if they have access
        if p.keybook_access:
            keybooks.append(ebook_data) # Reusing similar structure for keybooks for now
        
    books = []
    for sname, classes in series_dict.items():
        books.append({'series': sname, 'class_num': ', '.join(sorted(set(classes)))})
        
    purchased_series = [{'value': s, 'label': s} for s in purchased_series_set]
    
    syllabuses = Syllabus.objects.filter(school=school).order_by('-uploaded_at')
    shared_qps = SharedQuestionPaper.objects.filter(school=school).order_by('-uploaded_at')
    other_details = OtherDetails.objects.filter(school=school).order_by('-uploaded_at')
    
    return render(request, 'school_dashboard.html', {
        'school': school,
        'books': books,
        'ebooks': ebooks,
        'keybooks': keybooks,
        'purchased_series': purchased_series,
        'has_keybook_access': has_keybook_access,
        'has_qp_access': has_qp_access,
        'syllabuses': syllabuses,
        'shared_qps': shared_qps,
        'other_details': other_details,
    })
def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        if username == 'admin' and password == 'admin123':
            request.session['is_admin'] = True
            return redirect('admin_dashboard')
        else:
            return render(request, 'admin_login.html', {'error': 'Invalid username or password'})
    return render(request, 'admin_login.html')
def admin_dashboard(request):
    import json
    from collections import defaultdict
    from django.core.paginator import Paginator
    
    total_schools = School.objects.count()
    total_books_assigned = PurchaseItems.objects.count()
    
    schools = School.objects.all()
    schools_data = [{'school_name': s.school_name, 'school_id': s.school_id, 'branch': s.branch if s.branch else ''} for s in schools]
    schools_autocomplete = json.dumps(schools_data)
    
    purchases_qs = PurchaseItems.objects.select_related('purchase__school', 'book')
    search_query = request.GET.get('search', '')
    
    if search_query:
        purchases_qs = purchases_qs.filter(purchase__school__school_name__icontains=search_query) | \
                       purchases_qs.filter(purchase__school__school_id__icontains=search_query)
                       
    school_books = defaultdict(lambda: {'school_name': '', 'school_id': '', 'series': defaultdict(list)})
    
    for pi in purchases_qs:
        sid = pi.purchase.school.school_id
        school_books[sid]['school_name'] = pi.purchase.school.school_name
        school_books[sid]['school_id'] = sid
        school_books[sid]['series'][pi.book.series_name].append(pi.book.class_field)
        
    items_list = list(school_books.values())
    for item in items_list:
        # Convert defaultdict to normal dict so template .items works
        normal_series = {}
        for sname in item['series']:
            normal_series[sname] = sorted(list(set(item['series'][sname])))
        item['series'] = normal_series
            
    paginator = Paginator(items_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    trend_labels = json.dumps(['Q1', 'Q2', 'Q3', 'Q4'])
    trend_data = json.dumps([10, 25, 45, total_books_assigned])
    series_labels = json.dumps(['I-Smart', 'I-Whizz', 'I-Bot'])
    series_data = json.dumps([30, 20, 50])
    
    syllabuses = Syllabus.objects.select_related('school').all().order_by('-uploaded_at')
    other_details = OtherDetails.objects.select_related('school').all().order_by('-uploaded_at')
    teacher_logs = TeacherLog.objects.all().order_by('-login_time')
    
    return render(request, 'admin_dashboard.html', {
        'total_schools': total_schools,
        'total_books_assigned': total_books_assigned,
        'schools_autocomplete': schools_autocomplete,
        'all_schools': schools,
        'page_obj': page_obj,
        'trend_labels': trend_labels,
        'trend_data': trend_data,
        'series_labels': series_labels,
        'series_data': series_data,
        'syllabuses': syllabuses,
        'other_details': other_details,
        'teacher_logs': teacher_logs,
    })

@csrf_exempt
def delete_teacher_log(request, pk):
    if request.method == 'POST':
        log = get_object_or_404(TeacherLog, pk=pk)
        log.delete()
        messages.success(request, 'Teacher log deleted successfully.')
    return redirect('admin_dashboard')
def super_admin(request):
    books = Books.objects.all()
    schools = School.objects.all()
    purchases_qs = PurchaseItems.objects.all().select_related('purchase', 'book', 'purchase__school')
    
    # Group by purchase_id
    grouped_purchases = {}
    for item in purchases_qs:
        pid = item.purchase.purchase_id
        if pid not in grouped_purchases:
            grouped_purchases[pid] = {
                'purchase_id': pid,
                'school': item.purchase.school,
                'valid_upto': item.valid_upto,
                'items': []
            }
        grouped_purchases[pid]['items'].append(item)
    
    purchases = list(grouped_purchases.values())
    
    # Get all distinct purchase IDs for autocomplete
    all_purchases = Purchase.objects.values_list('purchase_id', flat=True).distinct()
    
    return render(request, 'super_admin.html', {
        'books': books, 'schools': schools, 'purchases': purchases, 'all_purchases': all_purchases
    })
def super_admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        if username == 'superadmin' and password == 'superadmin123':
            request.session['is_super_admin'] = True
            return redirect('super_admin')
        else:
            return render(request, 'super_admin_login.html', {'error': 'Invalid username or password'})
    return render(request, 'super_admin_login.html')
def super_admin_logout(request): return render(request, 'super_admin_login.html')
def admin_logout(request): return render(request, 'admin_login.html')
def school_logout(request):
    if 'school_id' in request.session:
        del request.session['school_id']
    return redirect('school_login')

def get_next_registration_ids(request):
    """Returns the next auto-generated school_id and purchase_id."""
    import re
    existing_ids = School.objects.values_list('school_id', flat=True)
    max_num = 0
    for sid in existing_ids:
        match = re.fullmatch(r'S(\d+)', sid, re.IGNORECASE)
        if match:
            num = int(match.group(1))
            if num > max_num:
                max_num = num
    next_num = max_num + 1
    next_school_id = f'S{next_num:02d}'
    next_purchase_id = f'p{next_school_id}'
    return JsonResponse({'school_id': next_school_id, 'purchase_id': next_purchase_id})

def add_school(request):
    if request.method == 'POST':
        import re
        # Auto-generate school_id if not provided or regenerate to ensure continuity
        school_id = request.POST.get('school_id', '').strip()
        purchase_id = request.POST.get('purchase_id', '').strip()

        # Fallback: regenerate if somehow blank
        if not school_id:
            existing_ids = School.objects.values_list('school_id', flat=True)
            max_num = 0
            for sid in existing_ids:
                match = re.fullmatch(r'S(\d+)', sid, re.IGNORECASE)
                if match:
                    num = int(match.group(1))
                    if num > max_num:
                        max_num = num
            next_num = max_num + 1
            school_id = f'S{next_num:02d}'
            purchase_id = f'p{school_id}'

        school_name = request.POST.get('school_name')
        contact = request.POST.get('contact')
        branch = request.POST.get('branch')
        email = request.POST.get('email')
        contact_person = request.POST.get('contact_person')
        password_hash = request.POST.get('password_hash')
        school = School.objects.create(
            school_id=school_id, school_name=school_name,
            contact=contact, branch=branch, email=email,
            contact_person=contact_person, password_hash=password_hash
        )
        # Auto-create the linked Purchase record
        if purchase_id:
            Purchase.objects.get_or_create(
                purchase_id=purchase_id,
                defaults={'school': school, 'purchase_date': datetime.now().date()}
            )
        messages.success(request, f'School {school_id} added successfully with Purchase ID {purchase_id}.')
    return redirect('super_admin')

def edit_school(request, pk):
    if request.method == 'POST':
        school = get_object_or_404(School, pk=pk)
        school.school_name = request.POST.get('school_name')
        school.contact = request.POST.get('contact')
        school.branch = request.POST.get('branch')
        school.email = request.POST.get('email')
        school.contact_person = request.POST.get('contact_person')
        
        password_hash = request.POST.get('password_hash')
        if password_hash:
            school.password_hash = password_hash
            
        school.save()
        messages.success(request, 'School updated successfully.')
    return redirect('super_admin')

def delete_school(request, pk):
    school = get_object_or_404(School, pk=pk)
    school.delete()
    messages.success(request, 'School deleted successfully.')
    return redirect('super_admin')

def add_book(request):
    if request.method == 'POST':
        book_id = request.POST.get('book_id')
        series_name = request.POST.get('series_name')
        class_field = request.POST.get('class_field')
        if not book_id:
            book_id = request.POST.get('book_id_field') # In case of form weirdness
        if book_id:
            Books.objects.get_or_create(
                book_id=book_id, defaults={'series_name': series_name, 'class_field': class_field}
            )
            messages.success(request, 'Book added successfully.')
    return redirect('super_admin')

def edit_book(request, pk):
    if request.method == 'POST':
        book = get_object_or_404(Books, pk=pk)
        book.series_name = request.POST.get('series_name')
        book.class_field = request.POST.get('class_field')
        book.save()
        messages.success(request, 'Book updated successfully.')
    return redirect('super_admin')

def delete_book(request, pk):
    book = get_object_or_404(Books, pk=pk)
    book.delete()
    messages.success(request, 'Book deleted successfully.')
    return redirect('super_admin')

@csrf_exempt
def assign_books(request):
    if request.method == 'POST':
        school_id = request.POST.get('school_id')
        book_ids = request.POST.getlist('book_ids')
        school = get_object_or_404(School, pk=school_id)
        
        purchase_id = f"PUR-{school_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        purchase, created = Purchase.objects.get_or_create(
            purchase_id=purchase_id,
            defaults={'school': school, 'purchase_date': datetime.now().date()}
        )
        
        valid_upto = datetime.now().replace(year=datetime.now().year + 1).date()
        assigned_count = 0
        for bid in book_ids:
            try:
                book = Books.objects.get(pk=bid)
                PurchaseItems.objects.get_or_create(
                    purchase=purchase, book=book, 
                    defaults={'valid_upto': valid_upto, 'sent_to_school': True}
                )
                assigned_count += 1
            except Books.DoesNotExist:
                continue
                
        return JsonResponse({'success': True, 'message': f'{assigned_count} books assigned successfully to {school.school_name}'})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@csrf_exempt
def delete_purchase(request, pk): return JsonResponse({'success': True})

@csrf_exempt
def delete_school_purchases_admin(request, school_id):
    if request.method == 'POST':
        school = get_object_or_404(School, pk=school_id)
        PurchaseItems.objects.filter(purchase__school=school).delete()
        return JsonResponse({'success': True, 'message': 'All access revoked successfully.'})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def delete_purchase_super(request, pk):
    item = get_object_or_404(PurchaseItems, pk=pk)
    item.delete()
    messages.success(request, 'Purchase removed successfully.')
    return redirect('super_admin')

def assign_purchase_super(request):
    if request.method == 'POST':
        purchase_id = request.POST.get('purchase_id')
        school_id = request.POST.get('school_id')
        book_ids = request.POST.getlist('book_ids')
        valid_upto = request.POST.get('valid_upto')
        
        # New checkboxes
        ebook_access = request.POST.get('ebook_access') == 'true'
        keybook_access = request.POST.get('keybook_access') == 'true'
        question_paper_access = request.POST.get('question_paper_access') == 'true'
        
        school = get_object_or_404(School, pk=school_id)
        
        purchase, created = Purchase.objects.get_or_create(
            purchase_id=purchase_id,
            defaults={'school': school, 'purchase_date': datetime.now().date()}
        )
        
        assigned_count = 0
        for book_id in book_ids:
            try:
                book = Books.objects.get(pk=book_id)
                PurchaseItems.objects.update_or_create(
                    purchase=purchase, book=book,
                    defaults={
                        'valid_upto': valid_upto, 
                        'sent_to_school': False,
                        'ebook_access': ebook_access,
                        'keybook_access': keybook_access,
                        'question_paper_access': question_paper_access
                    }
                )
                assigned_count += 1
            except Books.DoesNotExist:
                continue
                
        return JsonResponse({'success': True, 'message': f'{assigned_count} books assigned successfully to {school.school_name}'})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

def get_school_info(request):
    search_val = request.GET.get('q', '').strip()
    if not search_val:
        return JsonResponse({'success': False, 'error': 'No query provided'})
    
    # Check if it's a purchase ID
    purchase = Purchase.objects.filter(purchase_id=search_val).first()
    if purchase:
        return JsonResponse({
            'success': True, 
            'school_id': purchase.school.school_id,
            'school_name': purchase.school.school_name,
            'branch': purchase.school.branch or 'N/A'
        })
        
    # Check if it's a school ID
    school = School.objects.filter(school_id=search_val).first()
    if school:
        return JsonResponse({
            'success': True, 
            'school_id': school.school_id,
            'school_name': school.school_name,
            'branch': school.branch or 'N/A'
        })
        
    return JsonResponse({'success': False, 'error': 'Not found'})

def get_order_summary(request):
    school_id = request.GET.get('school_id')
    if not school_id:
        return JsonResponse({'success': False, 'error': 'No school_id provided'})
    
    school = School.objects.filter(school_id=school_id).first()
    if not school:
        return JsonResponse({'success': False, 'error': 'School not found'})
        
    purchases = PurchaseItems.objects.filter(purchase__school=school).select_related('book')
    ebook_count = purchases.count()
    keybook_access = purchases.filter(keybook_access=True).exists()
    qp_access = purchases.filter(question_paper_access=True).exists()
    already_sent = purchases.filter(sent_to_school=True).exists()

    books_list = []
    for p in purchases:
        books_list.append(f"{p.book.series_name} (Class {p.book.class_field})")
        
    return JsonResponse({
        'success': True,
        'ebook_count': ebook_count,
        'keybook_access': keybook_access,
        'question_paper_access': qp_access,
        'already_sent': already_sent,
        'books_list': books_list
    })

@csrf_exempt
def send_ebooks_to_school(request):
    if request.method == 'POST':
        school_id = request.POST.get('school_id')
        if not school_id:
            return JsonResponse({'success': False, 'error': 'School ID required'})
        school = School.objects.filter(school_id=school_id).first()
        if not school:
            return JsonResponse({'success': False, 'error': 'School not found'})
            
        purchases = PurchaseItems.objects.filter(purchase__school=school)
        if purchases.exists():
            purchases.update(sent_to_school=True)
            return JsonResponse({'success': True, 'message': f'E-books successfully sent to {school.school_name}.'})
        else:
            return JsonResponse({'success': False, 'error': 'No books assigned to this school yet.'})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@csrf_exempt
def upload_syllabus(request):
    if request.method == 'POST':
        school_ids = request.POST.getlist('school_ids')
        file = request.FILES.get('file')
        if not school_ids or not file:
            messages.error(request, 'Please select at least one school and upload a file.')
            return redirect('admin_dashboard')
            
        schools = School.objects.filter(school_id__in=school_ids)
        for school in schools:
            Syllabus.objects.create(school=school, file=file)
        messages.success(request, f'Syllabus sent to {schools.count()} schools successfully.')
    return redirect('admin_dashboard')

@csrf_exempt
def revoke_syllabus(request, pk):
    if request.method == 'POST':
        syllabus = get_object_or_404(Syllabus, pk=pk)
        school_name = syllabus.school.school_name
        syllabus.delete()
        messages.success(request, f'Syllabus revoked for {school_name}.')
    return redirect('admin_dashboard')

@csrf_exempt
def upload_question_paper(request):
    if request.method == 'POST':
        exam_type = request.POST.get('exam_type')
        school_ids = request.POST.getlist('school_ids')
        file = request.FILES.get('file')
        
        if not exam_type or not school_ids or not file:
            messages.error(request, 'Exam type, schools, and file are required.')
            return redirect('admin_dashboard')
            
        count = 0
        for sid in school_ids:
            school = School.objects.filter(pk=sid).first()
            if school:
                SharedQuestionPaper.objects.create(school=school, exam_type=exam_type, file=file)
                count += 1
                
        messages.success(request, f'Question paper sent to {count} schools successfully.')
    return redirect('admin_dashboard')

@csrf_exempt
def upload_other_details(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        school_ids = request.POST.getlist('school_ids')
        file = request.FILES.get('file')
        
        if not title or not school_ids or not file:
            messages.error(request, 'Title, schools, and file are required.')
            return redirect('admin_dashboard')
            
        count = 0
        for sid in school_ids:
            school = School.objects.filter(pk=sid).first()
            if school:
                OtherDetails.objects.create(school=school, title=title, file=file)
                count += 1
                
        messages.success(request, f'Other Details sent to {count} schools successfully.')
    return redirect('admin_dashboard')

@csrf_exempt
def revoke_other_details(request, pk):
    if request.method == 'POST':
        detail = get_object_or_404(OtherDetails, pk=pk)
        school_name = detail.school.school_name
        detail.delete()
        messages.success(request, f'Other Details revoked for {school_name}.')
    return redirect('admin_dashboard')

def get_book_chapters(request): return JsonResponse({'success': True})

@csrf_exempt
def generate_paper(request): 
    return render(request, 'generated_paper.html')

def download_paper_pdf(request): return HttpResponse("PDF File")

@csrf_exempt
def upload_announcement(request): return JsonResponse({'success': True})
@csrf_exempt
def delete_announcement(request, pk): return JsonResponse({'success': True})

@csrf_exempt
def send_otp(request): return JsonResponse({'success': True})
@csrf_exempt
def verify_otp(request): return JsonResponse({'success': True})
@csrf_exempt
def order_form(request): return render(request, 'orderform.html')
@csrf_exempt
def submit_order(request): return JsonResponse({'success': True})


BOOKS_DATA = {
    'ibot-series': {
        'title': 'I-BOT SERIES',
        'logo': 'images/ibotlogo.png',
        'tagline': 'Shaping Future Innovators in AI and Robotics',
        'description': "A comprehensive collection of 9 titles, the I-Bot series is designed to equip students with future-ready skills in AI, robotics, and programming. Covering the latest AI and robotics syllabus, the series also introduces core programming concepts in C, C++, HTML5, and Python, building a strong technical foundation for learners. For higher classes, students explore advanced topics such as cybersecurity, emerging technologies, wireless networking, and IoT, helping them stay aligned with the evolving digital world. At the primary level, the series focuses on strengthening logical thinking through algorithms, flowcharts, and hands-on coding using ScratchJr and Scratch 3.0. With a well-structured, progressive approach, the I-Bot series ensures a seamless learning journey to empower students at every stage to understand, apply, and excel in AI, robotics, and programming languages.",
        'bullets': [
            "A comprehensive collection of 9 titles, the I-Bot series is designed to equip students with future-ready skills in AI, robotics, and programming.",
            "Covering the latest AI and robotics syllabus, the series also introduces core programming concepts in C, C++, HTML5, and Python, building a strong technical foundation for learners.",
            "For higher classes, students explore advanced topics such as cybersecurity, emerging technologies, wireless networking, and IoT, helping them stay aligned with the evolving digital world.",
            "At the primary level, the series focuses on strengthening logical thinking through algorithms, flowcharts, and hands-on coding using ScratchJr and Scratch 3.0.",
            "With a well-structured, progressive approach, the I-Bot series ensures a seamless learning journey to empower students at every stage to understand, apply, and excel in AI, robotics, and programming languages."
        ],
        'books': {
            'class-1': {'title': 'Standard 1', 'image': 'images/ibot1.jpg', 'desc': 'Introduces young learners to smart machines, basic computer parts, and early coding concepts using ScratchJr.', 'details': ['Introduces young learners to smart machines, basic computer parts, and early coding concepts using ScratchJr.', 'Build a strong foundation in this topic, ideal for real-world application and academic excellence.']},
            'class-2': {'title': 'Standard 2', 'image': 'images/ibot2.jpg', 'desc': 'Building on basics, exploring input/output devices, and intermediate creative projects.', 'details': ['Building on basics, exploring input/output devices, and intermediate creative projects.', 'Empower students with practical skills in this topic, designed to foster creativity and logical thinking.']},
            'class-3': {'title': 'Standard 3', 'image': 'images/ibot3.jpg', 'desc': 'Understanding OS environments, word processing, and an introduction to computational thinking.', 'details': ['Understanding OS environments, word processing, and an introduction to computational thinking.', 'Empower students with practical skills in this topic, perfect for building modern digital fluency.']},
            'class-4': {'title': 'Standard 4', 'image': 'images/ibot4.jpg', 'desc': 'Advanced word processing, safe internet browsing, and block-based programming exercises.', 'details': ['Advanced word processing, safe internet browsing, and block-based programming exercises.', 'Empower students with practical skills in this topic, equipping students with tools for future success.']},
            'class-5': {'title': 'Standard 5', 'image': 'images/ibot5.jpg', 'desc': 'Presentations, spreadsheets basics, and developing algorithms using visual coding tools.', 'details': ['Presentations, spreadsheets basics, and developing algorithms using visual coding tools.', 'Interactive, hands-on activities covering this topic, encouraging problem-solving and critical reasoning.']},
            'class-6': {'title': 'Standard 6', 'image': 'images/ibot6.jpg', 'desc': 'Deep dive into robotics principles, electronics basics, and intro to Python syntax.', 'details': ['Deep dive into robotics principles, electronics basics, and intro to Python syntax.', 'Step-by-step guidance on this topic, equipping students with tools for future success.']},
            'class-7': {'title': 'Standard 7', 'image': 'images/ibot7.jpg', 'desc': 'AI concepts, intermediate Python programming, and hardware integration projects.', 'details': ['AI concepts, intermediate Python programming, and hardware integration projects.', 'Comprehensive coverage of this topic, designed to foster creativity and logical thinking.']},
            'class-8': {'title': 'Standard 8', 'image': 'images/ibot8.jpg', 'desc': 'Advanced robotics, IoT fundamentals, and machine learning basics.', 'details': ['Advanced robotics, IoT fundamentals, and machine learning basics.', 'Engaging lessons tailored for this topic, encouraging problem-solving and critical reasoning.']},
            'class-9': {'title': 'Standard 9', 'image': 'images/ibot9.jpg', 'desc': 'Comprehensive IT matrix, app development, and specialized AI/ML problem solving.', 'details': ['Comprehensive IT matrix, app development, and specialized AI/ML problem solving.', 'Build a strong foundation in this topic, creating an enjoyable and engaging learning environment.']},
        }
    },
    'ismart-series': {
        'title': 'I-SMART SERIES',
        'logo': 'images/iSmart Logo.png',
        'tagline': 'Smart Learning for a Digital Generation',
        'description': 'The I-Smart Series is a thoughtfully designed collection of 9 course titles that introduces students to a modern, tech-driven, and academic curriculum.\n\nAt the primary level, learners build strong fundamentals through topics such as Windows 10, MS Paint, Logo Programming, and Microsoft Office tools (Word, PowerPoint, and Excel 2010).\n\nAs students progress to higher grades, the series expands into advanced concepts, including HTML, C++ programming, JavaScript, MySQL, and Python, equipping them with essential coding and digital skills.\n\nWhat sets the I-Smart Series apart is its learner-friendly approach, featuring "Hint" sections and interactive "Do You Know?" and "Do It Yourself (DIY)" activities designed to reinforce understanding through practical application.\n\nWith a structured and progressive learning path, the I-Smart Series empowers students to build confidence, think logically, and stay ahead in today’s digital world.',
        'bullets': [
            'The I-Smart Series is a thoughtfully designed collection of 9 course titles that introduces students to a modern, tech-driven, and academic curriculum.',
            'At the primary level, learners build strong fundamentals through topics such as Windows 10, MS Paint, Logo Programming, and Microsoft Office tools (Word, PowerPoint, and Excel 2010).',
            'As students progress to higher grades, the series expands into advanced concepts, including HTML, C++ programming, JavaScript, MySQL, and Python, equipping them with essential coding and digital skills.',
            'What sets the I-Smart Series apart is its learner-friendly approach, featuring "Hint" sections and interactive "Do You Know?" and "Do It Yourself (DIY)" activities designed to reinforce understanding through practical application.',
            'With a structured and progressive learning path, the I-Smart Series empowers students to build confidence, think logically, and stay ahead in today’s digital world.'
        ],
        'books': {
            'level-1': {'title': 'Standard 1', 'image': 'images/ism1.jpg', 'desc': 'Foundations of smart learning and digital literacy.', 'details': ['Foundations of smart learning and digital literacy.', 'A fun, comprehensive approach to this topic, helping learners grasp complex topics with ease.']},
            'level-2': {'title': 'Standard 2', 'image': 'images/ism2.jpg', 'desc': 'Interactive exercises building core IT competencies.', 'details': ['Interactive exercises building core IT competencies.', 'Dive deep into this topic, perfect for building modern digital fluency.']},
            'level-3': {'title': 'Standard 3', 'image': 'images/ism3.jpg', 'desc': 'Exploring creative software and basic problem solving.', 'details': ['Exploring creative software and basic problem solving.', 'Step-by-step guidance on this topic, perfect for building modern digital fluency.']},
            'level-4': {'title': 'Standard 4', 'image': 'images/ism4.jpg', 'desc': 'Introduction to connected devices and cyber safety.', 'details': ['Introduction to connected devices and cyber safety.', 'Master the essentials of this topic, creating an enjoyable and engaging learning environment.']},
            'level-5': {'title': 'Standard 5', 'image': 'images/ism5.jpg', 'desc': 'Advanced office tools and beginner coding loops.', 'details': ['Advanced office tools and beginner coding loops.', 'A fun, comprehensive approach to this topic, designed to foster creativity and logical thinking.']},
            'level-6': {'title': 'Standard 6', 'image': 'images/ism6.jpg', 'desc': 'Structuring ideas and intermediate algorithmic logic.', 'details': ['Structuring ideas and intermediate algorithmic logic.', 'Empower students with practical skills in this topic, ideal for real-world application and academic excellence.']},
            'level-7': {'title': 'Standard 7', 'image': 'images/ism7.jpg', 'desc': 'Web technologies and introductory networking.', 'details': ['Web technologies and introductory networking.', 'Step-by-step guidance on this topic, designed to foster creativity and logical thinking.']},
            'level-8': {'title': 'Standard 8', 'image': 'images/ism8.jpg', 'desc': 'Data handling, analysis, and programming constructs.', 'details': ['Data handling, analysis, and programming constructs.', 'Comprehensive coverage of this topic, encouraging problem-solving and critical reasoning.']},
            'level-9': {'title': 'Standard 9', 'image': 'images/ism9.jpg', 'desc': 'Comprehensive system design and applied technology projects.', 'details': ['Comprehensive system design and applied technology projects.', 'Dive deep into this topic, perfect for building modern digital fluency.']},
        }
    },
    'iwhizz-series': {
        'title': 'I-WHIZZ SERIES',
        'logo': 'images/iWhizz Logo.png',
        'tagline': 'Accelerating Skills for a Tech-Driven World',
        'description': 'The I-Whizz Series features a collection of 9 courses, designed to build strong technical foundations across different grade levels.\n\nStudents begin with essential concepts such as computer fundamentals, Windows 7 OS, and the Office 2007 Suite, gaining a solid understanding of everyday digital tools.\n\nAs they progress, learners explore creative and technical skills through hands-on exposure to Photoshop, along with foundational programming in C and HTML.\n\nWith a structured, level-based approach, the I-Whizz Series helps students gradually develop practical knowledge, technical confidence, and the skills needed to thrive in a digital-first environment.',
        'bullets': [
            'The I-Whizz Series features a collection of 9 courses, designed to build strong technical foundations across different grade levels.',
            'Students begin with essential concepts such as computer fundamentals, Windows 7 OS, and the Office 2007 Suite, gaining a solid understanding of everyday digital tools.',
            'As they progress, learners explore creative and technical skills through hands-on exposure to Photoshop, along with foundational programming in C and HTML.',
            'With a structured, level-based approach, the I-Whizz Series helps students gradually develop practical knowledge, technical confidence, and the skills needed to thrive in a digital-first environment.'
        ],
        'books': {
            'class-1': {'title': 'Standard 1', 'image': 'images/iwhizz1.jpg', 'desc': 'Early steps into the world of tech and logic.', 'details': ['Early steps into the world of tech and logic.', 'A fun, comprehensive approach to this topic, designed to foster creativity and logical thinking.']},
            'class-2': {'title': 'Standard 2', 'image': 'images/iwhizz2.jpg', 'desc': 'Building foundational computer operation skills.', 'details': ['Building foundational computer operation skills.', 'Step-by-step guidance on this topic, equipping students with tools for future success.']},
            'class-3': {'title': 'Standard 3', 'image': 'images/iwhizz3.jpg', 'desc': 'Logical puzzles and introducing digital creativity.', 'details': ['Logical puzzles and introducing digital creativity.', 'Master the essentials of this topic, equipping students with tools for future success.']},
            'class-4': {'title': 'Standard 4', 'image': 'images/iwhizz4.jpg', 'desc': 'Word processing and exploring the internet safely.', 'details': ['Word processing and exploring the internet safely.', 'Dive deep into this topic, ensuring students stay ahead in today\'s tech-driven landscape.']},
            'class-5': {'title': 'Standard 5', 'image': 'images/iwhizz5.jpg', 'desc': 'Presentation tools and beginning programming principles.', 'details': ['Presentation tools and beginning programming principles.', 'Build a strong foundation in this topic, designed to foster creativity and logical thinking.']},
            'class-6': {'title': 'Standard 6', 'image': 'images/iwhizz6.jpg', 'desc': 'Deeper dive into software apps and coding techniques.', 'details': ['Deeper dive into software apps and coding techniques.', 'Empower students with practical skills in this topic, ensuring students stay ahead in today\'s tech-driven landscape.']},
            'class-7': {'title': 'Standard 7', 'image': 'images/iwhizz7.jpg', 'desc': 'Advanced digital tools and structured logic building.', 'details': ['Advanced digital tools and structured logic building.', 'Interactive, hands-on activities covering this topic, ideal for real-world application and academic excellence.']},
            'class-8': {'title': 'Standard 8', 'image': 'images/iwhizz8.jpg', 'desc': 'Web design basics and advanced conceptual frameworks.', 'details': ['Web design basics and advanced conceptual frameworks.', 'Interactive, hands-on activities covering this topic, perfect for building modern digital fluency.']},
            'class-9': {'title': 'Standard 9', 'image': 'images/iwhizz9.jpg', 'desc': 'Comprehensive studies in modern computing architectures.', 'details': ['Comprehensive studies in modern computing architectures.', 'Step-by-step guidance on this topic, equipping students with tools for future success.']},
        }
    },
    'young-wizard-series': {
        'title': 'YOUNG WIZARD SERIES',
        'logo': 'images/younglogo.jpg',
        'tagline': 'Where Young Minds Learn, Create, and Explore',
        'description': 'The Young Wizard Series is a vibrant collection of 5 course titles, specially designed for primary learners across Levels 1 to 5.\n\nWith its colorful, activity-based approach, the series makes learning fun and engaging while building strong digital foundations. Students are introduced to essential concepts such as the Windows 7 operating system, MS Word 2007, and Paint, along with basic graphical and animation skills.\n\nAs learners progress, they gain hands-on experience in working across platforms, exploring multimedia tools, internet browsing, and creative applications like SwishMax and Macromedia Flash.\n\nBlending creativity with technology, the Young Wizard Series offers a well-rounded digital-first learning experience, helping young minds develop confidence, curiosity, and essential computer skills from an early age.',
        'bullets': [
            'The Young Wizard Series is a vibrant collection of 5 course titles, specially designed for primary learners across Levels 1 to 5.',
            'With its colorful, activity-based approach, the series makes learning fun and engaging while building strong digital foundations. Students are introduced to essential concepts such as the Windows 7 operating system, MS Word 2007, and Paint, along with basic graphical and animation skills.',
            'As learners progress, they gain hands-on experience in working across platforms, exploring multimedia tools, internet browsing, and creative applications like SwishMax and Macromedia Flash.',
            'Blending creativity with technology, the Young Wizard Series offers a well-rounded digital-first learning experience, helping young minds develop confidence, curiosity, and essential computer skills from an early age.'
        ],
        'books': {
            'level-1': {'title': 'Level 1', 'image': 'images/young1.jpg', 'desc': 'Magical introduction to computers.', 'details': ['Magical introduction to computers.', 'Master the essentials of this topic, equipping students with tools for future success.']},
            'level-2': {'title': 'Level 2', 'image': 'images/young2.jpg', 'desc': 'Exploring creative tech tools.', 'details': ['Exploring creative tech tools.', 'Build a strong foundation in this topic, helping learners grasp complex topics with ease.']},
            'level-3': {'title': 'Level 3', 'image': 'images/young3.jpg', 'desc': 'Building logic through fun exercises.', 'details': ['Building logic through fun exercises.', 'A fun, comprehensive approach to this topic, ideal for real-world application and academic excellence.']},
            'level-4': {'title': 'Level 4', 'image': 'images/young4.jpg', 'desc': 'Intermediate magical computing tasks.', 'details': ['Intermediate magical computing tasks.', 'Engaging lessons tailored for this topic, encouraging problem-solving and critical reasoning.']},
            'level-5': {'title': 'Level 5', 'image': 'images/young5.jpg', 'desc': 'Advanced puzzles and digital mastery.', 'details': ['Advanced puzzles and digital mastery.', 'Comprehensive coverage of this topic, creating an enjoyable and engaging learning environment.']},
        }
    },
    'little-wizard-series': {
        'title': 'LITTLE WIZARD SERIES',
        'logo': 'images/little wizard series.png',
        'tagline': 'First Steps into the Digital World.',
        'description': 'The Little Wizard Series has been specially designed for early learners, featuring 2 course levels tailored for KG students.\n\nCreated to support teachers, students, and parents, the series delivers an interactive, fun, and engaging digital-first learning experience. With a focus on simple concepts and hands-on activities, it introduces young minds to the basics of technology in an enjoyable and accessible way.\n\nBlending learning with play, the Little Wizard Series offers a well-rounded foundation through practical exposure and engaging content, helping children take their first confident steps into the digital world.',
        'bullets': [
            'The Little Wizard Series has been specially designed for early learners, featuring 2 course levels tailored for KG students.',
            'Created to support teachers, students, and parents, the series delivers an interactive, fun, and engaging digital-first learning experience. With a focus on simple concepts and hands-on activities, it introduces young minds to the basics of technology in an enjoyable and accessible way.',
            'Blending learning with play, the Little Wizard Series offers a well-rounded foundation through practical exposure and engaging content, helping children take their first confident steps into the digital world.'
        ],
        'books': {
            'level-1': {'title': 'Kids Level 1', 'image': 'images/Kids level 1 wrapper.jpg', 'desc': 'Colorful shapes and mouse control.', 'details': ['Colorful shapes and mouse control.', 'Interactive, hands-on activities covering this topic, creating an enjoyable and engaging learning environment.']},
            'level-2': {'title': 'Kids Level 2', 'image': 'images/Kids level 2 wrapper.jpg', 'desc': 'Typing games and early logic.', 'details': ['Typing games and early logic.', 'Interactive, hands-on activities covering this topic, ensuring students stay ahead in today\'s tech-driven landscape.']},
        }
    },
    'app2016-series': {
        'title': 'Application 2016 Series',
        'logo': 'images/NEW APPLICATION SERIES.png',
        'tagline': 'From Basics to Brilliance in Office Tools. Learn. Apply. Excel.',
        'description': 'Designed to build practical digital skills, the Application Series 2016 offers an in-depth understanding of widely used application tools such as Microsoft Word, Excel, and PowerPoint 2016.\n\nEach application is explored individually through real-world illustrations and hands-on practice activities, making it easier for learners to grasp concepts and apply them confidently.\n\nThe series also provides strong conceptual coverage of MS Office tools, including Word, Excel, PowerPoint, and Access (2007 editions), ensuring a well-rounded foundation in productivity software.\n\nWith a structured and practical approach, this series helps learners develop both technical proficiency and real-world application skills essential for academic and professional success.',
        'bullets': [
            'Designed to build practical digital skills, the Application Series 2016 offers an in-depth understanding of widely used application tools such as Microsoft Word, Excel, and PowerPoint 2016.',
            'Each application is explored individually through real-world illustrations and hands-on practice activities, making it easier for learners to grasp concepts and apply them confidently.',
            'The series also provides strong conceptual coverage of MS Office tools, including Word, Excel, PowerPoint, and Access (2007 editions), ensuring a well-rounded foundation in productivity software.',
            'With a structured and practical approach, this series helps learners develop both technical proficiency and real-world application skills essential for academic and professional success.'
        ],
        'books': {
            'word': {'title': 'MS-Word 2016', 'image': 'images/2016 word.png', 'desc': 'Professional document creation and formatting.', 'details': ['Professional document creation and formatting.', 'Dive deep into this topic, ensuring students stay ahead in today\'s tech-driven landscape.']},
            'excel': {'title': 'MS-Excel 2016', 'image': 'images/2016 excel.png', 'desc': 'Data analysis, charting, and advanced functions.', 'details': ['Data analysis, charting, and advanced functions.', 'A fun, comprehensive approach to this topic, equipping students with tools for future success.']},
            'ppt': {'title': 'MS-PowerPoint 2016', 'image': 'images/2016 ppt.png', 'desc': 'Create stunning presentations with modern tools.', 'details': ['Create stunning presentations with modern tools.', 'A fun, comprehensive approach to this topic, ideal for real-world application and academic excellence.']},
        }
    },
    'app2007-series': {
        'title': 'Application 2007 Series',
        'logo': 'images/NEW APPLICATION SERIES.png',
        'tagline': 'Comprehensive Guide to the Classic Office 2007 Suite',
        'description': 'The Application Series 2007 is designed to develop practical digital skills by offering a clear understanding of widely used tools like Microsoft Office, Word, Excel, PowerPoint, and Access.\n\nEach application is covered individually through real-world examples and hands-on exercises, helping learners grasp concepts easily and apply them with confidence. The series also builds a strong foundation in MS Office with a structured, practical approach that supports both academic and professional success.',
        'books': {
            'office-2007': {'title': 'MS-Office 2007', 'image': 'images/App4.jpg', 'desc': 'Foundations of Office 2007 applications.', 'details': ['Foundations of Office 2007 applications.', 'Master the essentials of this topic, ensuring students stay ahead in today\'s tech-driven landscape.']},
            'word-2007': {'title': 'MS-Word 2007', 'image': 'images/App1.jpg', 'desc': 'Intermediate skills in Word and formatting.', 'details': ['Intermediate skills in Word formatting.', 'Dive deep into this topic, ensuring students stay ahead in today\'s tech-driven landscape.']},
            'excel-2007': {'title': 'MS-Excel 2007', 'image': 'images/App3.jpg', 'desc': 'Advanced formulas and spreadsheets.', 'details': ['Advanced formulas and spreadsheets.', 'Master the essentials of this topic, ideal for real-world application and academic excellence.']},
            'ppt-2007': {'title': 'MS-PowerPoint 2007', 'image': 'images/App5.jpg', 'desc': 'Creating dynamic presentations.', 'details': ['Creating dynamic presentations.', 'Unlock your potential with this topic, ensuring students stay ahead in today\'s tech-driven landscape.']},
            'access-2007': {'title': 'MS-Access 2007', 'image': 'images/App2.jpg', 'desc': 'Database management introduction.', 'details': ['Database management introduction.', 'Empower students with practical skills in this topic, designed to foster creativity and logical thinking.']},
        }
    },
    'programming-series': {
        'title': 'PROGRAMMING SERIES',
        'logo': 'images/programming series logo.jpeg',
        'tagline': 'Master the Code. Build the Future',
        'description': 'The Programming Series features a focused collection of single-color titles that’s designed to build strong programming fundamentals through hands-on learning.\n\nCovering key languages and tools such as HTML, Macromedia Flash, Microsoft Visual Basic, C, and C++, each book emphasizes practical exercises and real-world applications to help learners understand and apply concepts effectively.\n\nWith a clear, practice-driven approach, the series enables students to develop coding confidence and problem-solving skills essential for today’s digital landscape.',
        'bullets': [
            'The Programming Series features a focused collection of single-color titles that’s designed to build strong programming fundamentals through hands-on learning.',
            'Covering key languages and tools such as HTML, Macromedia Flash, Microsoft Visual Basic, C, and C++, each book emphasizes practical exercises and real-world applications to help learners understand and apply concepts effectively.',
            'With a clear, practice-driven approach, the series enables students to develop coding confidence and problem-solving skills essential for today’s digital landscape.'
        ],
        'books': {
            'level-1': {'title': 'C++ Programming', 'image': 'images/Pro1 New.jpg', 'desc': 'The fundamentals of coding and syntax.', 'details': ['The fundamentals of coding and syntax.', 'Interactive, hands-on activities covering this topic, creating an enjoyable and engaging learning environment.']},
            'level-2': {'title': 'C Programming', 'image': 'images/Pro2.jpg', 'desc': 'Data structures and algorithms introduction.', 'details': ['Data structures and algorithms introduction.', 'A fun, comprehensive approach to this topic, designed to foster creativity and logical thinking.']},
            'level-3': {'title': 'Multimedia Flash', 'image': 'images/Pro3.jpg', 'desc': 'Object-oriented concepts and design.', 'details': ['Object-oriented concepts and design.', 'Engaging lessons tailored for this topic, encouraging problem-solving and critical reasoning.']},
            'level-4': {'title': 'Learning HTML', 'image': 'images/Pro4 New.jpg', 'desc': 'Advanced applied programming techniques.', 'details': ['Advanced applied programming techniques.', 'Build a strong foundation in this topic, helping learners grasp complex topics with ease.']},
        }
    },
    'my-computer-series': {
        'title': 'MY COMPUTER SERIES',
        'logo': 'images/MyComputer Series (Grade).jpg',
        'tagline': 'Building Digital Foundations from Day One',
        'description': 'The My Computer Series is a thoughtfully designed set of 5 course titles for primary learners, covering Grades 1 to 5.\n\nWith vibrant visuals and activity-based workbooks, this series makes early computer learning fun, interactive, and easy to understand. Students are introduced to essential digital concepts, including the Windows operating system (with versions like XP) and its everyday applications.\n\nLearners also gain hands-on experience with tools such as MS Paint and WordPad and basic web design skill sets, helping them build confidence in using computers from an early stage.\n\nOver a strong focus on foundational skills and practical learning, the My Computer Series sets the stage for a smooth and engaging digital learning journey.',
        'bullets': [
            'The My Computer Series is a thoughtfully designed set of 5 course titles for primary learners, covering Grades 1 to 5.',
            'With vibrant visuals and activity-based workbooks, this series makes early computer learning fun, interactive, and easy to understand. Students are introduced to essential digital concepts, including the Windows operating system (with versions like XP) and its everyday applications.',
            'Learners also gain hands-on experience with tools such as MS Paint and WordPad and basic web design skill sets, helping them build confidence in using computers from an early stage.',
            'Over a strong focus on foundational skills and practical learning, the My Computer Series sets the stage for a smooth and engaging digital learning journey.'
        ],
        'books': {
            'level-1': {'title': 'Grade 1', 'image': 'images/my1.jpg', 'desc': 'Exploring your first PC.', 'details': ['Exploring your first PC.', 'Unlock your potential with this topic, ensuring students stay ahead in today\'s tech-driven landscape.']},
            'level-2': {'title': 'Grade 2', 'image': 'images/my2.jpg', 'desc': 'Handling files and folders safely.', 'details': ['Handling files and folders safely.', 'Unlock your potential with this topic, creating an enjoyable and engaging learning environment.']},
            'level-3': {'title': 'Grade 3', 'image': 'images/my3.jpg', 'desc': 'Navigating operating systems.', 'details': ['Navigating operating systems.', 'Unlock your potential with this topic, encouraging problem-solving and critical reasoning.']},
            'level-4': {'title': 'Grade 4', 'image': 'images/my4.jpg', 'desc': 'Settings, customization, and tools.', 'details': ['Settings, customization, and tools.', 'Interactive, hands-on activities covering this topic, encouraging problem-solving and critical reasoning.']},
            'level-5': {'title': 'Grade 5', 'image': 'images/my5.jpg', 'desc': 'System maintenance and troubleshooting.', 'details': ['System maintenance and troubleshooting.', 'Master the essentials of this topic, ideal for real-world application and academic excellence.']},
        }
    },
    'right-click-series': {
        'title': 'RIGHT-CLICK SERIES',
        'logo': 'images/right click series.png',
        'logo_margin': '0px',
        'tagline': 'Empowering Students in The World of Right-Click',
        'description': 'The Right-Click Series is designed to build strong foundations in Information and Communication Technology (ICT) for students from Grades 6 to 9.\n\nCovering the Windows operating system, essential application tools, and key programming concepts, the series introduces learners to basic programming, Visual fundamentals, and practical IT applications.\n\nWith a structured, curriculum-aligned approach, the Right-Click Series helps students develop essential digital skills, logical thinking, and real-world computer proficiency, preparing them for today’s technology-driven environment.',
        'bullets': [
            'The Right-Click Series is designed to build strong foundations in Information and Communication Technology (ICT) for students from Grades 6 to 9.',
            'Covering the Windows operating system, essential application tools, and key programming concepts, the series introduces learners to basic programming, Visual fundamentals, and practical IT applications.',
            'With a structured, curriculum-aligned approach, the Right-Click Series helps students develop essential digital skills, logical thinking, and real-world computer proficiency, preparing them for today’s technology-driven environment.'
        ],
        'books': {
            'level-6': {'title': 'ICT Standard 6', 'image': 'images/ict6.jpg', 'desc': 'Information and Communication Tech basics.', 'details': ['Information and Communication Tech basics.', 'Step-by-step guidance on this topic, designed to foster creativity and logical thinking.']},
            'level-7': {'title': 'ICT Standard 7', 'image': 'images/ict7.jpg', 'desc': 'Networks and data communication.', 'details': ['Networks and data communication.', 'Interactive, hands-on activities covering this topic, ideal for real-world application and academic excellence.']},
            'level-8': {'title': 'ICT Standard 8', 'image': 'images/ict8.jpg', 'desc': 'Applied IT systems in the real world.', 'details': ['Applied IT systems in the real world.', 'Empower students with practical skills in this topic, encouraging problem-solving and critical reasoning.']},
            'level-9': {'title': 'ICT Standard 9', 'image': 'images/ict9.jpg', 'desc': 'Comprehensive technology integration.', 'details': ['Comprehensive technology integration.', 'Dive deep into this topic, designed to foster creativity and logical thinking.']},
        }
    },
    'cursive-writing-books': {
        'title': 'MY FIRST STROKE SERIES',
        'logo': 'images/cursive writing.png',
        'tagline': 'Enriching Cursive Hands With Linguistic Differentiations. One Stroke at a Time.',
        'description': 'My First Stroke Series is a thoughtfully designed collection of 7 cursive writing books in English and Tamil, crafted for learners from LKG to Grade 5.\n\nWith a step-by-step approach, the series helps students develop clear, neat, and confident handwriting. It covers everything from lowercase and uppercase letters to word formation and sentence writing, inclusive of Tamil letters, in both short and long forms.\n\nThrough guided practice and structured exercises, the series builds strong writing habits—making learning cursive both effective and enjoyable for young learners.',
        'bullets': [
            'My First Stroke Series is a thoughtfully designed collection of 7 cursive writing books in English and Tamil, crafted for learners from LKG to Grade 5.',
            'With a step-by-step approach, the series helps students develop clear, neat, and confident handwriting. It covers everything from lowercase and uppercase letters to word formation and sentence writing, inclusive of Tamil letters, in both short and long forms.',
            'Through guided practice and structured exercises, the series builds strong writing habits—making learning cursive both effective and enjoyable for young learners.'
        ],
        'books': {
            'lkg': {'title': 'Cursive Writing LKG', 'image': 'images/cursive-lkg.jpg', 'desc': 'Introduction to strokes and basic patterns.', 'details': ['Introduction to strokes and basic patterns.', 'Build a strong foundation in this topic, equipping students with tools for future success.']},
            'ukg': {'title': 'Cursive Writing UKG', 'image': 'images/cursive-ukg.jpg', 'desc': 'Building letter forms and simple connections.', 'details': ['Building letter forms and simple connections.', 'Engaging lessons tailored for this topic, designed to foster creativity and logical thinking.']},
            'level-1': {'title': 'Level 1', 'image': 'images/Level 1.jpg', 'desc': 'Fluid word formation and sentence structure.', 'details': ['Fluid word formation and sentence structure.', 'A fun, comprehensive approach to this topic, helping learners grasp complex topics with ease.']},
            'level-2': {'title': 'Level 2', 'image': 'images/Level 2.jpg', 'desc': 'Advanced penmanship and consistent spacing.', 'details': ['Advanced penmanship and consistent spacing.', 'Interactive, hands-on activities covering this topic, ensuring students stay ahead in today\'s tech-driven landscape.']},
            'level-3': {'title': 'Level 3', 'image': 'images/Level 3.jpg', 'desc': 'Perfecting the elegant cursive script.', 'details': ['Perfecting the elegant cursive script.', 'A fun, comprehensive approach to this topic, creating an enjoyable and engaging learning environment.']},
            'level-4': {'title': 'Level 4', 'image': 'images/Level 4.jpg', 'desc': 'Creative writing in professional cursive.', 'details': ['Creative writing in professional cursive.', 'Build a strong foundation in this topic, perfect for building modern digital fluency.']},
            'level-5': {'title': 'Level 5', 'image': 'images/Level 5.jpg', 'desc': 'Mastery of decorative and formal penmanship.', 'details': ['Mastery of decorative and formal penmanship.', 'A fun, comprehensive approach to this topic, helping learners grasp complex topics with ease.']},
        }
    },
    'tamil-writing-books': {
        'title': 'Tamil Copy Writing Series',
        'logo': 'images/my first.jpeg',
        'tagline': 'A beautiful journey into Tamil calligraphy and structured writing practice.',
        'description': 'At the basic level, Tamil copywriting books are often designed for students and beginners to learn letter formation, improve handwriting, and develop sentence construction skills. These books provide structured exercises that help readers practice Tamil scripts, join letters into words, and gradually build fluency in writing.\n\nOverall, Tamil copywriting books serve as a bridge between language proficiency and creative communication, enabling individuals to write effectively in Tamil—whether for education, storytelling, or business-driven content.',
        'books': {
            'level-1': {'title': 'L.K.G', 'image': 'images/tamil1.jpg', 'desc': 'Basic Tamil characters and stroke techniques.', 'details': ['Basic Tamil characters and stroke techniques.', 'Master the essentials of this topic, creating an enjoyable and engaging learning environment.']},
            'level-2': {'title': 'U.K.G', 'image': 'images/tamil2.jpg', 'desc': 'Building words and understanding letter structures.', 'details': ['Building words and understanding letter structures.', 'Build a strong foundation in this topic, designed to foster creativity and logical thinking.']},
            'level-3': {'title': 'முதல் நிலை', 'image': 'images/tamil3.jpg', 'desc': 'Intermediate word formation and sentence patterns.', 'details': ['Intermediate word formation and sentence patterns.', 'Engaging lessons tailored for this topic, ensuring students stay ahead in today\'s tech-driven landscape.']},
            'level-4': {'title': 'இரண்டாம் நிலை', 'image': 'images/tamil4.jpg', 'desc': 'Enhancing writing speed and letter consistency.', 'details': ['Enhancing writing speed and letter consistency.', 'Unlock your potential with this topic, encouraging problem-solving and critical reasoning.']},
            'level-5': {'title': 'மூன்றாம் நிலை', 'image': 'images/tamil5.jpg', 'desc': 'Advanced copy writing and literary phrases.', 'details': ['Advanced copy writing and literary phrases.', 'A fun, comprehensive approach to this topic, equipping students with tools for future success.']},
            'level-6': {'title': 'நான்காம் நிலை', 'image': 'images/tamil6.jpg', 'desc': 'Perfecting the flow of Tamil script.', 'details': ['Perfecting the flow of Tamil script.', 'A fun, comprehensive approach to this topic, encouraging problem-solving and critical reasoning.']},
            'level-7': {'title': 'ஐந்தாம் நிலை', 'image': 'images/tamil7.jpg', 'desc': 'Mastery of formal Tamil calligraphy.', 'details': ['Mastery of formal Tamil calligraphy.', 'Engaging lessons tailored for this topic, ideal for real-world application and academic excellence.']},
        }
    }
}



def series_detail(request, series_slug):
    series = BOOKS_DATA.get(series_slug)
    if not series: return render(request, 'products.html')
    return render(request, 'series_detail.html', {'series_slug': series_slug, 'series': series})

def book_detail(request, series_slug, book_slug):
    series = BOOKS_DATA.get(series_slug)
    if not series: return render(request, 'products.html')
    book = series['books'].get(book_slug)
    if not book: return render(request, 'series_detail.html', {'series_slug': series_slug, 'series': series})
    return render(request, 'book_detail.html', {'series_slug': series_slug, 'book_slug': book_slug, 'series': series, 'book': book})
