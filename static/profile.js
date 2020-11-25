/*

Profile page event handler

*/

const accountSections = document.querySelectorAll(".account-section")
const accountMenu = document.querySelector("#account-menu")

// Display the account details section on load
window.onload = () => {
    accountSections[0].style.display = "block"
}

// Change which menu section is active within the UI
accountMenu.onclick = (el) => {
    menu = el.target.parentNode.children

    // Prevent clicking on disabled buttons
    if (!el.target.classList.value.includes("disabled")) {

        // Activates selected section
        deactivateItem()
        el.target.classList.add("active")

        // Retrieves the index of the item clicked
        index = 0
        for (item of menu) {
            if (item.innerText == el.target.innerText) {
                break
            }
            index++
        }

        // Changes to the selected section using its id
        changeSection(index)
    }
}

// Remove active styling from every menu item
function deactivateItem() {
    tabs = accountMenu.children
    for (tab of tabs) {
        tab.classList.remove("active")
    }
}

// Change active section selected from the menu
function changeSection(index) {
    for (item of accountSections) {
        item.style.display = "none"
    }

    accountSections[index].style.display = "block"
}