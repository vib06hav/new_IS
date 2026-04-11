const POPUP_WIDTH = 480;
const POPUP_HEIGHT = 760;

function buildPopupFeatures() {
  const dualScreenLeft = window.screenLeft ?? 0;
  const dualScreenTop = window.screenTop ?? 0;
  const viewportWidth = window.innerWidth || document.documentElement.clientWidth || screen.width;
  const viewportHeight = window.innerHeight || document.documentElement.clientHeight || screen.height;
  const left = Math.max(dualScreenLeft + viewportWidth - POPUP_WIDTH - 32, dualScreenLeft);
  const top = Math.max(dualScreenTop + 40, dualScreenTop);

  return [
    `width=${POPUP_WIDTH}`,
    `height=${POPUP_HEIGHT}`,
    `left=${left}`,
    `top=${top}`,
    "resizable=yes",
    "scrollbars=yes",
  ].join(",");
}

export function openInterviewPopup(applicationId: string) {
  const popup = window.open(
    `/interviewer/applications/${applicationId}/overlay`,
    `interview-overlay-${applicationId}`,
    buildPopupFeatures(),
  );

  if (popup) {
    popup.focus();
  }

  return popup;
}

export function openInterviewPopupPlaceholder(applicationId: string) {
  const popup = window.open("", `interview-overlay-${applicationId}`, buildPopupFeatures());
  if (popup) {
    popup.document.title = "Opening interview overlay...";
    popup.document.body.style.margin = "0";
    popup.document.body.style.fontFamily = "system-ui, sans-serif";
    popup.document.body.innerHTML =
      "<div style='padding:24px;color:#0f172a;background:#f8fafc;min-height:100vh;'>Opening interview overlay...</div>";
    popup.focus();
  }
  return popup;
}
