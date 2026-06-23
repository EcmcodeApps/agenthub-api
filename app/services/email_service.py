"""
Servicio de email vía SendGrid.
Si SENDGRID_API_KEY no está configurada, registra el email en consola (modo dev).
"""

import logging
from app.core.config import get_settings

logger = logging.getLogger(__name__)


async def send_team_invitation(
    to_email: str,
    inviter_name: str,
    org_name: str,
    role: str,
    invite_link: str,
) -> bool:
    """Envía correo de invitación al equipo. Retorna True si se envió."""
    settings = get_settings()

    subject = f"{inviter_name} te invitó a {org_name} en AgentHub"

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8"/>
      <meta name="viewport" content="width=device-width, initial-scale=1"/>
    </head>
    <body style="margin:0;padding:0;background:#f4f4f5;font-family:Inter,Arial,sans-serif;">
      <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f5;padding:40px 0;">
        <tr>
          <td align="center">
            <table width="560" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
              <!-- Header -->
              <tr>
                <td style="background:#1a1a2e;padding:32px 40px;text-align:center;">
                  <p style="margin:0;font-size:22px;font-weight:700;color:#ffffff;letter-spacing:-0.5px;">
                    AgentHub <span style="color:#7c3aed;">Empresarial</span>
                  </p>
                </td>
              </tr>
              <!-- Body -->
              <tr>
                <td style="padding:40px;">
                  <p style="font-size:24px;font-weight:700;color:#111827;margin:0 0 8px;">
                    Te han invitado al equipo
                  </p>
                  <p style="font-size:15px;color:#6b7280;margin:0 0 32px;line-height:1.6;">
                    <strong style="color:#111827;">{inviter_name}</strong> te ha invitado a unirte a
                    <strong style="color:#111827;">{org_name}</strong> en AgentHub Empresarial
                    con el rol de <strong style="color:#7c3aed;">{role}</strong>.
                  </p>

                  <table cellpadding="0" cellspacing="0" style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;padding:20px;margin-bottom:32px;width:100%;">
                    <tr>
                      <td>
                        <p style="margin:0 0 4px;font-size:11px;font-weight:700;color:#9ca3af;letter-spacing:1px;text-transform:uppercase;">Organización</p>
                        <p style="margin:0;font-size:16px;font-weight:700;color:#111827;">{org_name}</p>
                      </td>
                    </tr>
                    <tr><td style="height:12px;"></td></tr>
                    <tr>
                      <td>
                        <p style="margin:0 0 4px;font-size:11px;font-weight:700;color:#9ca3af;letter-spacing:1px;text-transform:uppercase;">Tu rol</p>
                        <p style="margin:0;font-size:16px;font-weight:700;color:#7c3aed;">{role}</p>
                      </td>
                    </tr>
                  </table>

                  <table cellpadding="0" cellspacing="0" style="margin-bottom:32px;">
                    <tr>
                      <td style="background:#7c3aed;border-radius:8px;padding:14px 28px;">
                        <a href="{invite_link}" style="color:#ffffff;font-size:15px;font-weight:700;text-decoration:none;">
                          Aceptar invitación →
                        </a>
                      </td>
                    </tr>
                  </table>

                  <p style="font-size:13px;color:#9ca3af;line-height:1.6;">
                    Si no esperabas esta invitación, puedes ignorar este correo.<br/>
                    El enlace expira en 7 días.
                  </p>
                </td>
              </tr>
              <!-- Footer -->
              <tr>
                <td style="background:#f9fafb;padding:20px 40px;border-top:1px solid #e5e7eb;">
                  <p style="margin:0;font-size:12px;color:#9ca3af;text-align:center;">
                    AgentHub Empresarial · Colombia · <a href="https://agenthub.co" style="color:#7c3aed;text-decoration:none;">agenthub.co</a>
                  </p>
                </td>
              </tr>
            </table>
          </td>
        </tr>
      </table>
    </body>
    </html>
    """

    if not settings.sendgrid_api_key:
        logger.warning(
            "[EMAIL - MODO DEV] Para: %s | Asunto: %s | Link: %s",
            to_email, subject, invite_link
        )
        return True  # En dev siempre "exitoso"

    try:
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.sendgrid.com/v3/mail/send",
                headers={
                    "Authorization": f"Bearer {settings.sendgrid_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "personalizations": [{"to": [{"email": to_email}]}],
                    "from": {
                        "email": settings.email_from,
                        "name": settings.email_from_name,
                    },
                    "subject": subject,
                    "content": [{"type": "text/html", "value": html}],
                },
                timeout=10.0,
            )
        if response.status_code == 202:
            logger.info("Email de invitación enviado a %s", to_email)
            return True
        else:
            logger.error("SendGrid error %s: %s", response.status_code, response.text)
            return False
    except Exception as e:
        logger.error("Error enviando email: %s", e)
        return False
