"""
Login OTP Action - Menjalankan alur login lengkap dengan OTP challenge.
Mendukung skip otomatis jika session masih valid melalui check_selector.
"""

import asyncio
from backend.actions.base_action import BaseAction, ExecutionContext, ActionResult, ActionStatus
from backend.actions.otp_challenge_action import OtpChallengeAction


class LoginOtpAction(BaseAction):
    """Login dengan username/password, kemudian verifikasi OTP."""

    @property
    def name(self) -> str:
        return "login_otp"

    @property
    def default_params(self) -> dict:
        return {
            "username_selector": "",
            "username_value": "",
            "password_selector": "",
            "password_value": "",
            "login_selector": "",
            "login_wait_until": "domcontentloaded",
            "otp_selector": "",
            "otp_submit_selector": "",
            "check_selector": "",
            "timeout": 30000,
            "wait_for_otp_timeout": 120000,
            "otp_length": 6,
            "otp_title": "Masukkan Kode OTP",
            "otp_description": "Cek SMS/email Anda dan masukkan kode OTP",
            "otp_auto_submit": True,
            "on_error": "stop",
        }

    def validate_params(self, params: dict) -> list[str]:
        errors = []
        if not params.get("username_selector"):
            errors.append("Parameter 'username_selector' wajib diisi.")
        if not params.get("username_value"):
            errors.append("Parameter 'username_value' wajib diisi.")
        if not params.get("password_selector"):
            errors.append("Parameter 'password_selector' wajib diisi.")
        if not params.get("password_value"):
            errors.append("Parameter 'password_value' wajib diisi.")
        if not params.get("login_selector"):
            errors.append("Parameter 'login_selector' wajib diisi.")
        otp_timeout = params.get("wait_for_otp_timeout", 120000)
        if not isinstance(otp_timeout, (int, float)) or otp_timeout <= 0:
            errors.append("Parameter 'wait_for_otp_timeout' harus berupa angka positif (ms).")
        return errors

    async def execute(self, context: ExecutionContext, params: dict) -> ActionResult:
        page = context.page
        if not page:
            return ActionResult(
                status=ActionStatus.FAILED,
                message="Tidak ada halaman browser yang aktif.",
            )

        username_selector = params.get("username_selector", "")
        username_value = params.get("username_value", "")
        password_selector = params.get("password_selector", "")
        password_value = params.get("password_value", "")
        login_selector = params.get("login_selector", "")
        login_wait_until = params.get("login_wait_until", "domcontentloaded")
        otp_selector = params.get("otp_selector", "")
        otp_submit_selector = params.get("otp_submit_selector", "")
        check_selector = params.get("check_selector", "")
        timeout = params.get("timeout", 30000)
        wait_for_otp_timeout = params.get("wait_for_otp_timeout", 120000)
        otp_length = params.get("otp_length", 6)
        otp_title = params.get("otp_title", "Masukkan Kode OTP")
        otp_description = params.get("otp_description", "Cek SMS/email Anda dan masukkan kode OTP")
        otp_auto_submit = params.get("otp_auto_submit", True)

        username_selector = self._substitute_variables(username_selector, context)
        username_value = self._substitute_variables(username_value, context)
        password_selector = self._substitute_variables(password_selector, context)
        password_value = self._substitute_variables(password_value, context)
        login_selector = self._substitute_variables(login_selector, context)
        if otp_selector:
            otp_selector = self._substitute_variables(otp_selector, context)
        if otp_submit_selector:
            otp_submit_selector = self._substitute_variables(otp_submit_selector, context)
        if check_selector:
            check_selector = self._substitute_variables(check_selector, context)

        if check_selector:
            try:
                existing = await page.query_selector(check_selector)
                if existing:
                    return ActionResult(
                        status=ActionStatus.SUCCESS,
                        message="Session masih valid, skip login.",
                        data={"skipped": True, "reason": "already_logged_in"},
                    )
            except Exception:
                pass

        try:
            username_play = self._convert_selector(username_selector, "css")
            password_play = self._convert_selector(password_selector, "css")
            login_play = self._convert_selector(login_selector, "css")

            await page.wait_for_selector(username_play, state="visible", timeout=timeout)
            await page.fill(username_play, username_value)

            await page.wait_for_selector(password_play, state="visible", timeout=timeout)
            await page.fill(password_play, password_value)

            await page.click(login_play)
            try:
                await page.wait_for_load_state(login_wait_until, timeout=timeout)
            except Exception:
                pass

            otp_action = OtpChallengeAction()
            otp_params = {
                "selector": otp_selector,
                "selector_type": "css",
                "submit_selector": otp_submit_selector,
                "timeout": wait_for_otp_timeout,
                "otp_length": otp_length,
                "title": otp_title,
                "description": otp_description,
                "auto_submit": otp_auto_submit,
            }
            otp_result = await otp_action.execute(context, otp_params)

            if otp_result.status == ActionStatus.FAILED:
                return ActionResult(
                    status=ActionStatus.FAILED,
                    message=f"Login gagal saat verifikasi OTP: {otp_result.message}",
                    error=otp_result.error,
                )

            return ActionResult(
                status=ActionStatus.SUCCESS,
                message="Login berhasil, OTP terverifikasi.",
                data={
                    "username": username_value,
                    "otp_verified": True,
                    "skipped": False,
                },
            )

        except Exception as e:
            return ActionResult(
                status=ActionStatus.FAILED,
                message=f"Gagal login: {str(e)}",
                error=str(e),
            )

    def _convert_selector(self, selector: str, selector_type: str) -> str:
        if selector_type == "xpath":
            return f"xpath={selector}"
        return selector

    def _substitute_variables(self, text: str, context: ExecutionContext) -> str:
        if "{{" not in text:
            return text
        result = text
        for key, value in context.current_data.items():
            result = result.replace(f"{{{{data.{key}}}}}", str(value))
        for key, value in context.variables.items():
            result = result.replace(f"{{{{variables.{key}}}}}", str(value))
        return result
