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
        extra_data = params.get("extra_data", {})
        wait_after = params.get("wait_after", 0)
        timeout = params.get("timeout", 10000)

        if wait_after > 0:
            await asyncio.sleep(wait_after / 1000)

        try:
            result = await page.evaluate("""async (args) => {
                const formSel = args.formSel;
                const submitSel = args.submitSel;
                const extra = args.extra;
                const form = document.querySelector(formSel);
                if (!form) return {error: 'Form not found: ' + formSel};

                const fd = new FormData(form);

                const data = {};
                for (const [k, v] of fd.entries()) {
                    if (data[k] !== undefined) {
                        if (!Array.isArray(data[k])) data[k] = [data[k]];
                        data[k].push(v);
                    } else {
                        data[k] = v;
                    }
                }

                for (const [k, v] of Object.entries(extra)) {
                    data[k] = v;
                }

                const submitBtn = submitSel ? document.querySelector(submitSel) : null;
                const actionUrl = submitBtn ? (submitBtn.formAction || form.action) : form.action;
                const method = submitBtn ? (submitBtn.formMethod || form.method || 'POST') : (form.method || 'POST');

                try {
                    const resp = await fetch(actionUrl, {
                        method: method.toUpperCase(),
                        body: new URLSearchParams(data),
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest',
                            'Accept': 'application/json',
                        },
                        credentials: 'same-origin',
                    });
                    const text = await resp.text();
                    return {url: actionUrl, status: resp.status, success: resp.ok, body: text};
                } catch (e) {
                    return {error: 'Fetch failed: ' + e.message};
                }
            }""", {"formSel": form_selector, "submitSel": submit_selector, "extra": extra_data})

            if "error" in result:
                return ActionResult(
                    status=ActionStatus.FAILED,
                    message=result["error"],
                    error=result["error"],
                )

            if result.get("success") or result.get("status") == 302:
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