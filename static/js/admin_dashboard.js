console.log("Admin Dashboard JS Loaded");

window.addSeries = function () {
    console.log("addSeries clicked");
    const dropdown = document.getElementById("series-dropdown");
    const container = document.getElementById("selected-series-container");
    const selectedSeries = dropdown.value;

    if (!selectedSeries) {
        alert("Please select a series first.");
        return;
    }

    // Check if already added
    if (document.getElementById(`series-block-${selectedSeries}`)) {
        alert("This series is already added.");
        return;
    }

    // Create Series Block
    const seriesBlock = document.createElement("div");
    seriesBlock.classList.add("card");
    seriesBlock.id = `series-block-${selectedSeries}`;
    seriesBlock.style.padding = "20px";
    seriesBlock.style.position = "relative";
    seriesBlock.style.borderLeft = "5px solid #e91e63";

    // Remove Button
    const removeBtn = document.createElement("button");
    removeBtn.innerHTML = "×";
    removeBtn.style.position = "absolute";
    removeBtn.style.top = "10px";
    removeBtn.style.right = "10px";
    removeBtn.style.background = "#ff5f5f";
    removeBtn.style.color = "white";
    removeBtn.style.border = "none";
    removeBtn.style.borderRadius = "50%";
    removeBtn.style.width = "25px";
    removeBtn.style.height = "25px";
    removeBtn.style.cursor = "pointer";
    removeBtn.onclick = function () {
        seriesBlock.remove();
        updateSummary();
    };

    // Title
    const title = document.createElement("h4");
    title.textContent = selectedSeries;
    title.style.margin = "0 0 15px 0";
    title.style.color = "#333";

    // Classes Container
    const classesContainer = document.createElement("div");
    classesContainer.style.display = "grid";
    classesContainer.style.gridTemplateColumns = "repeat(auto-fill, minmax(80px, 1fr))";
    classesContainer.style.gap = "10px";

    // Static Classes for UI Demo
    const staticClasses = ["Class 1", "Class 2", "Class 3", "Class 4", "Class 5"];

    staticClasses.forEach(cls => {
        const label = document.createElement("label");
        label.classList.add("checkbox-label");
        label.style.display = "flex";
        label.style.alignItems = "center";
        label.style.gap = "8px";
        label.style.fontSize = "14px";
        label.style.cursor = "pointer";

        const checkbox = document.createElement("input");
        checkbox.type = "checkbox";
        checkbox.name = "books"; // Just for show
        checkbox.value = `${selectedSeries} - ${cls}`;
        checkbox.onchange = updateSummary;

        label.appendChild(checkbox);
        label.appendChild(document.createTextNode(cls));
        classesContainer.appendChild(label);
    });

    seriesBlock.appendChild(removeBtn);
    seriesBlock.appendChild(title);
    seriesBlock.appendChild(classesContainer);
    container.appendChild(seriesBlock);

    updateSummary();
}

window.updateSummary = function () {
    const summaryList = document.getElementById("total-summary-list");
    summaryList.innerHTML = "";

    const checkboxes = document.querySelectorAll('input[name="books"]:checked');

    if (checkboxes.length === 0) {
        summaryList.innerHTML = "<li>No books selected yet.</li>";
        return;
    }

    checkboxes.forEach(cb => {
        const li = document.createElement("li");
        li.textContent = cb.value;
        li.style.borderBottom = "1px solid #eee";
        li.style.padding = "5px 0";
        summaryList.appendChild(li);
    });
}
