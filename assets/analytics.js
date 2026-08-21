/* GA4. One shared file so there is a single measurement ID, not 39 copies. */
(function () {
  var ID = "G-YH8ZYHGSXS";
  var s = document.createElement("script");
  s.async = true;
  s.src = "https://www.googletagmanager.com/gtag/js?id=" + ID;
  document.head.appendChild(s);
  window.dataLayer = window.dataLayer || [];
  window.gtag = function () { dataLayer.push(arguments); };
  gtag("js", new Date());
  gtag("config", ID);
})();
