function getThreadInfo() {
  let threadId = document
    .querySelector('[role="main"] [data-legacy-thread-id]')
    .getAttribute("data-legacy-thread-id");

  let email = null;
  const accountButton = document.querySelector(
    'a[href*="accounts.google.com/SignOutOptions"][aria-label]'
  );
  if (accountButton) {
    const ariaLabel = accountButton.getAttribute("aria-label");
    const emailMatch = ariaLabel.match(/\(([^)]+@[^)]+\.com)\)/);
    email = emailMatch ? emailMatch[1] : null;
  }

  console.log("Extracted Thread ID:", threadId);
  console.log("Extracted Email:", email);
  return { threadId, email };
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "getThreadInfo") {
    const threadInfo = getThreadInfo();
    console.log("Sending thread info:", threadInfo);
    sendResponse(threadInfo);
  }
  return true;
});
