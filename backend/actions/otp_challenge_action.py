"""
OTP Challenge Action - Menangani proses verifikasi OTP dengan dialog di browser.
Menginject modal HTML ke halaman, menunggu user memasukkan kode OTP, lalu mengembalikan nilainya.
"""

import asyncio
from backend.actions.base_action import BaseAction, ExecutionContext, ActionResult, ActionStatus


class OtpChallengeAction(BaseAction):
    """Menampilkan dialog OTP di browser dan menunggu input dari user."""

    @property
    def name(self) -> str:
        return "otp_challenge"

    @property
    def default_params(self) -> dict:
        return {
            "selector": "",
            "selector_type": "css",
            "submit_selector": "",
            "timeout": 120000,
            "otp_length": 6,
            "title": "Masukkan Kode OTP",
            "description": "Cek SMS/email Anda dan masukkan kode OTP",
            "auto_submit": True,
        }

    def validate_params(self, params: dict) -> list[str]:
        errors = []
        timeout = params.get("timeout", 120000)
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            errors.append("Parameter 'timeout' harus berupa angka positif (ms).")
        otp_length = params.get("otp_length", 6)
        if not isinstance(otp_length, int) or otp_length <= 0:
            errors.append("Parameter 'otp_length' harus berupa angka positif.")
        return errors

    async def execute(self, context: ExecutionContext, params: dict) -> ActionResult:
        page = context.page
        if not page:
            return ActionResult(
                status=ActionStatus.FAILED,
                message="Tidak ada halaman browser yang aktif.",
            )

        selector = params.get("selector", "")
        selector_type = params.get("selector_type", "css")
        submit_selector = params.get("submit_selector", "")
        timeout = params.get("timeout", 120000)
        otp_length = params.get("otp_length", 6)
        title = params.get("title", "Masukkan Kode OTP")
        description = params.get("description", "Cek SMS/email Anda dan masukkan kode OTP")
        auto_submit = params.get("auto_submit", True)

        play_selector = self._convert_selector(selector, selector_type) if selector else None

        try:
            await self._inject_otp_modal(page, title, description, otp_length, timeout)
            otp_value = await self._wait_for_otp_submission(page, timeout)

            if not otp_value:
                return ActionResult(
                    status=ActionStatus.FAILED,
                    message="OTP challenge dibatalkan atau timeout.",
                    error="OTP timeout or cancelled",
                )

            if play_selector:
                try:
                    await page.wait_for_selector(play_selector, state="visible", timeout=10000)
                    await page.fill(play_selector, otp_value)
                except Exception as e:
                    return ActionResult(
                        status=ActionStatus.FAILED,
                        message=f"Gagal mengisi OTP ke field '{selector}': {str(e)}",
                        error=str(e),
                    )

            if auto_submit and submit_selector:
                try:
                    await page.wait_for_selector(submit_selector, state="visible", timeout=5000)
                    await page.click(submit_selector)
                except Exception:
                    pass

            return ActionResult(
                status=ActionStatus.SUCCESS,
                message=f"OTP berhasil diproses.",
                data={"otp_length": len(otp_value), "auto_submit": auto_submit},
            )

        except Exception as e:
            return ActionResult(
                status=ActionStatus.FAILED,
                message=f"Gagal proses OTP challenge: {str(e)}",
                error=str(e),
            )

    async def _inject_otp_modal(self, page, title: str, description: str, otp_length: int, timeout: int):
        js_code = """
        (args) => {
            const existing = document.getElementById('automation-studio-otp-modal');
            if (existing) existing.remove();

            const overlay = document.createElement('div');
            overlay.id = 'automation-studio-otp-modal';
            overlay.style.cssText = `
                position: fixed; inset: 0; z-index: 999999;
                background: rgba(0,0,0,0.45); backdrop-filter: blur(2px);
                display: flex; align-items: center; justify-content: center;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            `;

            const card = document.createElement('div');
            card.style.cssText = `
                background: #fff; border-radius: 12px; padding: 24px 28px;
                width: 420px; max-width: 92vw; box-shadow: 0 20px 50px rgba(0,0,0,0.25);
                border: 1px solid #e5e7eb;
            `;

            card.innerHTML = `
                <h2 style="margin: 0 0 6px; font-size: 18px; color: #111827;">${args.title}</h2>
                <p style="margin: 0 0 18px; font-size: 13px; color: #6b7280;">${args.description}</p>
                <input id="automation-studio-otp-input" type="text" inputmode="numeric" autocomplete="one-time-code"
                    placeholder="Masukkan kode OTP" maxlength="${args.otpLength}"
                    style="width: 100%; padding: 10px 12px; border-radius: 8px; border: 1px solid #d1d5db;
                    font-size: 16px; letter-spacing: 4px; text-align: center; outline: none;
                    box-sizing: border-box;" />
                <div style="display: flex; justify-content: flex-end; gap: 10px; margin-top: 18px;">
                    <button id="automation-studio-otp-cancel" type="button"
                        style="padding: 8px 14px; border-radius: 6px; border: 1px solid #d1d5db;
                        background: #fff; color: #374151; font-size: 13px; cursor: pointer;">
                        Batal
                    </button>
                    <button id="automation-studio-otp-submit" type="button"
                        style="padding: 8px 14px; border-radius: 6px; border: none;
                        background: #2563eb; color: #fff; font-size: 13px; font-weight: 600; cursor: pointer;">
                        Verifikasi
                    </button>
                </div>
                <p id="automation-studio-otp-status" style="margin: 10px 0 0; font-size: 12px; color: #6b7280; text-align: center;"></p>
            `;

            overlay.appendChild(card);
            document.body.appendChild(overlay);

            const input = document.getElementById('automation-studio-otp-input');
            if (input) input.focus();

            window.__automationStudioOtpResolve = null;
            window.__automationStudioOtpPromise = new Promise((resolve) => {
                window.__automationStudioOtpResolve = resolve;
            });

            const submitBtn = document.getElementById('automation-studio-otp-submit');
            const cancelBtn = document.getElementById('automation-studio-otp-cancel');
            const statusEl = document.getElementById('automation-studio-otp-status');

            const close = (value) => {
                overlay.remove();
                resolve(value);
            };

            submitBtn.addEventListener('click', () => {
                const val = input.value.trim();
                if (!val) {
                    statusEl.textContent = 'Masukkan kode OTP terlebih dahulu.';
                    statusEl.style.color = '#ef4444';
                    return;
                }
                close(val);
            });

            cancelBtn.addEventListener('click', () => {
                close(null);
            });

            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') submitBtn.click();
                if (e.key === 'Escape') cancelBtn.click();
            });
        }
        """
        await page.evaluate(js_code, {
            "title": title,
            "description": description,
            "otpLength": otp_length,
        })

    async def _wait_for_otp_submission(self, page, timeout: int) -> str:
        try:
            result = await page.evaluate("""(timeout) => {
                return new Promise((resolve) => {
                    const start = Date.now();
                    const check = () => {
                        if (Date.now() - start > timeout) {
                            resolve(null);
                            return;
                        }
                        const modal = document.getElementById('automation-studio-otp-modal');
                        if (!modal) {
                            resolve(null);
                            return;
                        }
                        if (window.__automationStudioOtpResolve) {
                            resolve(window.__automationStudioOtpResolve);
                        } else {
                            setTimeout(check, 200);
                        }
                    };
                    check();
                });
            }""", timeout)
            return result or ""
        except Exception:
            return ""
