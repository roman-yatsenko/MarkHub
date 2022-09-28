window.MathJax = {
    tex: {
      inlineMath: [["\\(", "\\)"]],
      displayMath: [["\\[", "\\]"]],
      processEscapes: true,
      processEnvironments: true
    },
    options: {
      ignoreHtmlClass: ".*|",
      processHtmlClass: "arithmatex"
    }
  };
  
(function () {
  var script = document.createElement('script');
  script.src = 'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-svg.js';
  script.async = true;
  document.head.appendChild(script);
})();

let preview = document.getElementById("nav-preview-tab-content");

function previewContentChanged() {
  console.log('previewContentChanged');
  MathJax.typeset();
  setTimeout(MathJax.typeset, 5000);
}

if (preview) {
  preview.onclick = () => {
    setTimeout(previewContentChanged, 1000);
  }
}
