/**
 * Dr. Islam Akef Ebeid — Executive Portal Gmail Read-Only Bridge (Google Apps Script)
 * ====================================================================================
 * 1-Time Setup (takes ~2 minutes):
 *   1. Open https://script.google.com while signed into your Gmail account.
 *   2. Click "New project", name it "Executive Portal Gmail Bridge", and paste this file.
 *   3. Replace BRIDGE_SECRET below with your own strong random passphrase.
 *   4. Click Deploy -> New deployment -> Select type: Web app
 *        - Execute as: Me (your Gmail)
 *        - Who has access: Anyone
 *      (Access is strictly gated by your BRIDGE_SECRET token in the code below.)
 *   5. Authorize read-only Gmail access when prompted, copy the Web App URL
 *      (ends in /exec), and paste both the URL and BRIDGE_SECRET into the
 *      "Inbox Internal News" widget settings in your Executive Portal Dashboard.
 *
 * Security:
 *   - Strictly READ-ONLY (never modifies, deletes, or sends emails).
 *   - Rejects any request missing the exact BRIDGE_SECRET token.
 *   - Uses GET with query parameters so browser fetch() from GitHub Pages works
 *     with zero CORS preflight issues.
 */

const BRIDGE_SECRET = 'CHANGE_ME_TO_A_STRONG_SECRET_TOKEN';

function doGet(e) {
  try {
    const params = (e && e.parameter) || {};
    const token = String(params.token || '').trim();
    const expected = PropertiesService.getScriptProperties().getProperty('BRIDGE_SECRET') || BRIDGE_SECRET;

    if (!expected || expected === 'CHANGE_ME_TO_A_STRONG_SECRET_TOKEN') {
      return jsonOut({
        ok: false,
        error: 'Set BRIDGE_SECRET in your Google Apps Script before deploying.'
      });
    }
    if (!token || token !== expected) {
      return jsonOut({ ok: false, error: 'Unauthorized: invalid bridge token.' });
    }

    const days = Math.max(1, Math.min(30, parseInt(params.days || '7', 10) || 7));
    const limit = Math.max(1, Math.min(50, parseInt(params.limit || '25', 10) || 25));
    const unreadOnly = String(params.unread || 'false').toLowerCase() === 'true';

    const queryParts = ['in:inbox', `newer_than:${days}d`, '-category:promotions', '-category:social'];
    if (unreadOnly) queryParts.push('is:unread');
    const query = queryParts.join(' ');

    const threads = GmailApp.search(query, 0, limit);
    const items = [];
    let unreadCount = 0;

    for (let i = 0; i < threads.length; i++) {
      const th = threads[i];
      const msgs = th.getMessages();
      if (!msgs || !msgs.length) continue;
      const latest = msgs[msgs.length - 1];
      const isUnread = th.isUnread();
      if (isUnread) unreadCount++;

      const plainBody = (latest.getPlainBody() || '')
        .replace(/\r/g, '')
        .replace(/\n{3,}/g, '\n\n')
        .replace(/https?:\/\/\S{80,}/g, '[link]')
        .trim();

      const labels = th.getLabels().map(function (lb) { return lb.getName(); });
      const threadId = th.getId();

      items.push({
        id: latest.getId(),
        threadId: threadId,
        subject: th.getFirstMessageSubject() || '(No Subject)',
        from: latest.getFrom() || '',
        to: latest.getTo() || '',
        date: latest.getDate() ? latest.getDate().toISOString() : '',
        isUnread: isUnread,
        isStarred: th.hasStarredMessages(),
        messageCount: msgs.length,
        labels: labels,
        snippet: plainBody.slice(0, 220).replace(/\s+/g, ' ').trim(),
        bodyExcerpt: plainBody.slice(0, 900),
        permalink: 'https://mail.google.com/mail/u/0/#inbox/' + threadId
      });
    }

    return jsonOut({
      ok: true,
      account: Session.getActiveUser().getEmail() || 'Gmail Inbox',
      fetchedAt: new Date().toISOString(),
      query: query,
      days: days,
      totalReturned: items.length,
      unreadCount: unreadCount,
      emails: items
    });
  } catch (err) {
    return jsonOut({
      ok: false,
      error: String(err && err.message ? err.message : err)
    });
  }
}

function jsonOut(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
