"""
HTTP Submit Action - Submits form data directly via HTTP POST from the browser.
Bypasses Playwright's actionability & network-idle waiting for faster execution.
"""

import asyncio
from backend.actions.base_action import BaseAction, ExecutionContext, ActionResult, ActionStatus


class HttpSubmitAction(BaseAction):
    """Submits a form's data directly via HTTP POST from the browser tab."""

    @property
    def name(self) -> str:
        return "http_submit"

    @property
    def description(self) -> str:
        return "Submit form via HTTP POST from browser (bypass UI click)"

    @property
    def default_params(self) -> dict:
        return {
            "form_selector": "",
            "selector_type": "css",
            "submit_selector": "",
            "url": "",
            "extra_data": {},
            "wait_before": 0,
            "wait_after": 0,
            "timeout": 10000,
            "fallback_to_click": False,
        }

    def validate_params(self, params: dict) -> list[str]:
        errors = []
        if not params.get("form_selector"):
            errors.append("Parameter 'form_selector' wajib diisi.")
        return errors

    async def execute(self, context: ExecutionContext, params: dict) -> ActionResult:
        page = context.page
        if not page:
            return ActionResult(
                status=ActionStatus.FAILED,
                message="Tidak ada halaman browser yang aktif.",
            )

        form_selector = params.get("form_selector", "")
        submit_selector = params.get("submit_selector", "")
        url = params.get("url", "")
        extra_data = params.get("extra_data", {})
        wait_before = params.get("wait_before", 0)
        wait_after = params.get("wait_after", 0)
        timeout = params.get("timeout", 10000)
        fallback_to_click = params.get("fallback_to_click", False)

        if wait_before > 0:
            await asyncio.sleep(wait_before / 1000)

        http_result = None
        try:
            http_result = await page.evaluate("""async (args) => {
                const formSel = args.formSel;
                const submitSel = args.submitSel;
                const url = args.url;
                const extra = args.extra;
                const form = document.querySelector(formSel);
                if (!form) return {error: 'Form not found: ' + formSel};

                const fd = new FormData(form);

                for (const [k, v] of Object.entries(extra)) {
                    fd.append(k, v);
                }

                const submitBtn = submitSel ? document.querySelector(submitSel) : null;
                const actionUrl = url || (submitBtn ? (submitBtn.formAction || form.action) : form.action);
                const method = submitBtn ? (submitBtn.formMethod || form.method || 'POST') : (form.method || 'POST');

                if (!actionUrl) return {error: 'Submit URL not found. Set form action, submit formAction, or pass url parameter.'};

                try {
                    const resp = await fetch(actionUrl, {
                        method: method.toUpperCase(),
                        body: fd,
                        credentials: 'same-origin',
                    });
                    const text = await resp.text();
                    let parsed = null;
                    try { parsed = JSON.parse(text); } catch (e) { parsed = text; }
                    
                    if (typeof $ !== 'undefined' && typeof $.unblockUI === 'function') {
                        $.unblockUI();
                    }
                    
                    return {url: actionUrl, status: resp.status, success: resp.ok, body: text, parsed: parsed};
                } catch (e) {
                    if (typeof $ !== 'undefined' && typeof $.unblockUI === 'function') {
                        $.unblockUI();
                    }
                    return {error: 'Fetch failed: ' + e.message};
                }
            }""", {"formSel": form_selector, "submitSel": submit_selector, "url": url, "extra": extra_data})

            if "error" in http_result:
                if fallback_to_click and submit_selector:
                    return await self._fallback_click_submit(page, submit_selector, wait_after)
                return ActionResult(
                    status=ActionStatus.FAILED,
                    message=http_result["error"],
                    error=http_result["error"],
                )

            if http_result.get("success") or http_result.get("status") == 302:
                parsed = http_result.get("parsed")
                if isinstance(parsed, dict) and parsed.get("Status") is False:
                    if fallback_to_click and submit_selector:
                        return await self._fallback_click_submit(page, submit_selector, wait_after)
                    return ActionResult(
                        status=ActionStatus.FAILED,
                        message="Server menolak submit: {}".format(parsed.get("Pesan", "Unknown error")),
                        error="Business logic error",
                        data={"server_response": parsed},
                    )
                
                if wait_after > 0:
                    await asyncio.sleep(wait_after / 1000)
                
                return ActionResult(
                    status=ActionStatus.SUCCESS,
                    message="HTTP submit berhasil (status {})".format(http_result.get("status")),
                    data={
                        "url": http_result.get("url"),
                        "status": http_result.get("status"),
                        "fields_submitted": len(http_result.get("body", "")),
                    },
                )

            if fallback_to_click and submit_selector:
                return await self._fallback_click_submit(page, submit_selector, wait_after)

            return ActionResult(
                status=ActionStatus.FAILED,
                message="HTTP submit gagal: status {} - {}".format(
                    http_result.get("status"), http_result.get("body", "")[:500]
                ),
                error="HTTP {}".format(http_result.get("status")),
            )

        except Exception as e:
            if fallback_to_click and submit_selector:
                return await self._fallback_click_submit(page, submit_selector, wait_after)
            return ActionResult(
                status=ActionStatus.FAILED,
                message="Gagal HTTP submit: {}".format(str(e)),
                error=str(e),
            )

    async def _fallback_click_submit(self, page, submit_selector: str, wait_after: int = 0):
        """Fallback: klik tombol submit jika HTTP submit gagal."""
        try:
            await page.wait_for_selector(submit_selector, state="visible", timeout=10000)
            await page.locator(submit_selector).first.click()
            if wait_after > 0:
                await asyncio.sleep(wait_after / 1000)
            return ActionResult(
                status=ActionStatus.SUCCESS,
                message="Submit berhasil via fallback click",
                data={"fallback": True},
            )
        except Exception as e:
            return ActionResult(
                status=ActionStatus.FAILED,
                message="Fallback click submit gagal: {}".format(str(e)),
                error=str(e),
            )