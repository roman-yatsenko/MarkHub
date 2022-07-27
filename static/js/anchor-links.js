// anchor link processing
document.addEventListener("click", function(event) {
    var element = event.target;
    if (element.tagName.toLowerCase() == "a" && 
        element.getAttribute("href").indexOf("#") === 0) {
      element.href = location.href.split("#")[0] + element.getAttribute("href");
    }
});
