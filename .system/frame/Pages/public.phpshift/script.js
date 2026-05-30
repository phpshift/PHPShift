document.querySelectorAll(".share-card").forEach((card) => {
  card.addEventListener("click", async () => {
    var link = card.getAttribute("share");
    var textEl = card.querySelector(".overlay span");

    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(link);
      } else {
        var tempInput = document.createElement("input");
        document.body.appendChild(tempInput);
        tempInput.value = link;
        tempInput.select();
        document.execCommand("copy");
        document.body.removeChild(tempInput);
      }

      textEl.textContent = "Copied!";

      setTimeout(() => {
        textEl.textContent = "Share";
      }, 1500);
    } catch (err) {
      console.log("Copy failed:", err);
      textEl.textContent = "Copy failed";
    }
  });
});
