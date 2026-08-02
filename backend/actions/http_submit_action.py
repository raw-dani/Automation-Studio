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
            "wait_after": 0,
            "timeout": 10000,
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
        wait_after = params.get("wait_after", 0)
        timeout = params.get("timeout", 10000)

        if wait_after > 0:
            await asyncio.sleep(wait_after / 1000)

        try:
            result = await page.evaluate("""async (args) => {
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
                    return {url: actionUrl, status: resp.status, success: resp.ok, body: text, parsed: parsed};
                } catch (e) {
                    return {error: 'Fetch failed: ' + e.message};
                }
            }""", {"formSel": form_selector, "submitSel": submit_selector, "url": url, "extra": extra_data})

            if "error" in result:
                return ActionResult(
                    status=ActionStatus.FAILED,
                    message=result["error"],
                    error=result["error"],
                )

            if result.get("success") or result.get("status") == 302:
                parsed = result.get("parsed")
                if isinstance(parsed, dict) and parsed.get("Status") is False:
                    return ActionResult(
                        status=ActionStatus.FAILED,
                        message="Server menolak submit: {}".format(parsed.get("Pesan", "Unknown error")),
                        error="Business logic error",
                        data={"server_response": parsed},
                    )
                return ActionResult(
                    status=ActionStatus.SUCCESS,
                    message="HTTP submit berhasil (status {})".format(result.get("status")),
                    data={
                        "url": result.get("url"),
                        "status": result.get("status"),
                        "fields_submitted": len(result.get("body", "")),
                    },
                )

            return ActionResult(
                status=ActionStatus.FAILED,
                message="HTTP submit gagal: status {} - {}".format(
                    result.get("status"), result.get("body", "")[:500]
                ),
                error="HTTP {}".format(result.get("status")),
            )

        except Exception as e:
            return ActionResult(
                status=ActionStatus.FAILED,
                message="Gagal HTTP submit: {}".format(str(e)),
                error=str(e),
            )