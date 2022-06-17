// Press power action button
const powerActions = document.querySelectorAll('.power-action');
powerActions.forEach((target) => {
  target.addEventListener("click", (e) => {
    const powerStatus = e.target.name;
    setPower(powerStatus);
  })
});

// Close button on top message box
const closeTopMessage = document.getElementById("close-top-message-box");
closeTopMessage.addEventListener("click", () => {
  const topMessageBox = document.getElementById("top-message-box");
  topMessageBox.style.display = "none";
});

// Change navigation
const menuItems = document.querySelectorAll(".menu-item");
menuItems.forEach((target) => {
  target.addEventListener("click", (e) => {
    resetActiveItem();
    e.target.classList.add("active");
    changeSubPage(e.target);
  })
});

// Change sub pages
const changeSubPage = (targetPage) => {
  const subPages = document.querySelectorAll(".sub-page");
  subPages.forEach((target) => {
    if (targetPage.name === target.attributes.name.nodeValue) {
      target.classList.remove("invisible");
    } else {
      target.classList.add("invisible");
    }
  })
};

// Reset navigation select
const resetActiveItem = () => {
  menuItems.forEach((target) => {
    target.classList.remove("active")
  });
};
