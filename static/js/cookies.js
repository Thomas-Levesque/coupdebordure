// static/js/cookies.js
(function () {
  const KEY = "cdb_cookie_consent_v1";

  function readConsent() {
    try { return JSON.parse(localStorage.getItem(KEY) || ""); }
    catch { return null; }
  }

  function writeConsent(consent) {
    const payload = {
      essential: true,
      analytics: !!consent.analytics,
      ads: !!consent.ads,
      ts: Date.now(),
      v: 1,
    };
    localStorage.setItem(KEY, JSON.stringify(payload));
    writeConsentCookies(payload);   // ✅ NEW
  }

  // ✅ NEW: write cookies readable by Django
  function setCookie(name, value, days) {
    const maxAge = days * 24 * 60 * 60;
    document.cookie = `${encodeURIComponent(name)}=${encodeURIComponent(value)}; Path=/; Max-Age=${maxAge}; SameSite=Lax`;
  }

  function writeConsentCookies(payload) {
    // cookies simples "true/false" pour le serveur
    setCookie("cdb_ads", payload.ads ? "true" : "false", 180);
    setCookie("cdb_analytics", payload.analytics ? "true" : "false", 180);
  }

  function showBanner() {
    const el = document.getElementById("cookie-banner");
    if (el) el.style.display = "block";
  }

  function hideBanner() {
    const el = document.getElementById("cookie-banner");
    if (el) el.style.display = "none";
  }

  window.CDBCookies = {
    get: readConsent,
    reset: function () {
      localStorage.removeItem(KEY);
      // reset cookies aussi
      setCookie("cdb_ads", "false", 180);
      setCookie("cdb_analytics", "false", 180);
      showBanner();
      // optionnel: refresh pour enlever les pubs
      location.reload();
    }
  };

  function enableScripts(consent) {
    window.dispatchEvent(new CustomEvent("cdb:cookie-consent", { detail: consent }));
  }

  function init() {
    const existing = readConsent();
    if (!existing) {
      showBanner();
    } else {
      // au cas où tu avais du localStorage sans cookies avant
      writeConsentCookies(existing);
      enableScripts(existing);
    }

    const btnAccept = document.getElementById("cookie-accept");
    const btnReject = document.getElementById("cookie-reject");
    const btnCustomize = document.getElementById("cookie-customize");
    const btnSave = document.getElementById("cookie-save");
    const details = document.getElementById("cookie-details");
    const cbAnalytics = document.getElementById("cookie-analytics");
    const cbAds = document.getElementById("cookie-ads");

    if (!btnAccept) return;

    btnAccept.addEventListener("click", () => {
      const consent = { analytics: true, ads: true };
      writeConsent(consent);
      hideBanner();
      enableScripts(readConsent());
      location.reload(); // ✅ IMPORTANT: pour que Django masque/affiche les pubs
    });

    btnReject.addEventListener("click", () => {
      const consent = { analytics: false, ads: false };
      writeConsent(consent);
      hideBanner();
      enableScripts(readConsent());
      location.reload(); // ✅ IMPORTANT
    });

    btnCustomize.addEventListener("click", () => {
      if (!details) return;
      const isOpen = details.style.display === "block";
      details.style.display = isOpen ? "none" : "block";

      const cur = readConsent();
      if (cur) {
        if (cbAnalytics) cbAnalytics.checked = !!cur.analytics;
        if (cbAds) cbAds.checked = !!cur.ads;
      }

      btnAccept.style.display = "none";
      btnReject.style.display = "none";
      btnCustomize.style.display = "none";
      btnSave.style.display = "inline-flex";
    });

    btnSave.addEventListener("click", () => {
      const consent = {
        analytics: cbAnalytics ? cbAnalytics.checked : false,
        ads: cbAds ? cbAds.checked : false,
      };
      writeConsent(consent);
      hideBanner();
      enableScripts(readConsent());
      location.reload(); // ✅ IMPORTANT
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();