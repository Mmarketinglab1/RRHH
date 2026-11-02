import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings


def format_expiration_es(dt: datetime | None) -> str:
    if not dt:
        return "Sin fecha límite definida"
    return dt.strftime("%d/%m/%Y %H:%M")


def build_survey_notification_email(
    *,
    evaluation_title: str,
    evaluator_name: str,
    evaluatee_name: str,
    relationship_label: str,
    survey_url: str,
    expires_at: datetime | None,
    custom_message: str | None = None,
    subject_override: str | None = None,
) -> tuple[str, str, str]:
    subject = subject_override or f"Aviso de Encuesta 360°: {evaluation_title}"
    subject = subject.replace("{evaluation_title}", evaluation_title).replace("{evaluatee_name}", evaluatee_name)

    exp_str = format_expiration_es(expires_at)
    is_self = relationship_label.lower() in ("self", "autoevaluación", "autoevaluacion")
    target_desc = (
        "tu <strong>Autoevaluación</strong>"
        if is_self
        else f"la evaluación de <strong>{evaluatee_name}</strong> ({relationship_label})"
    )
    target_desc_plain = (
        "tu Autoevaluación"
        if is_self
        else f"la evaluación de {evaluatee_name} ({relationship_label})"
    )

    custom_block_html = ""
    custom_block_plain = ""
    if custom_message and custom_message.strip():
        clean_msg = custom_message.strip()
        custom_block_html = f"""
        <div style="background-color: #f8fafc; border-left: 4px solid #00857c; padding: 12px 16px; margin: 16px 0; color: #334155; font-size: 14px;">
          {clean_msg}
        </div>
        """
        custom_block_plain = f"\nMensaje del organizador:\n{clean_msg}\n"

    expiration_html = ""
    expiration_plain = ""
    if expires_at:
        expiration_html = f"""
        <div style="background-color: #fff8e6; border: 1px solid #ffe58f; border-radius: 8px; padding: 12px 16px; margin: 16px 0; color: #875800; font-size: 14px;">
          ⏰ <strong>Fecha de caducidad de la encuesta:</strong> {exp_str}
        </div>
        """
        expiration_plain = f"\nFecha de caducidad de la encuesta: {exp_str}\n"

    html_body = f"""
    <!DOCTYPE html>
    <html>
      <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif; color: #1e293b; line-height: 1.6; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="border: 1px solid #e2e8f0; border-radius: 12px; padding: 28px; background: #ffffff;">
          <div style="font-size: 12px; font-weight: 700; text-transform: uppercase; color: #00857c; letter-spacing: 0.5px;">
            RRHH 360 • Evaluación de Desempeño
          </div>
          <h2 style="margin: 8px 0 16px; color: #0f172a;">{evaluation_title}</h2>
          <p>Hola <strong>{evaluator_name}</strong>,</p>
          <p>Te invitamos a completar {target_desc} dentro del proceso <strong>{evaluation_title}</strong>.</p>
          {custom_block_html}
          {expiration_html}
          <div style="margin: 24px 0; text-align: center;">
            <a href="{survey_url}" style="background-color: #00857c; color: #ffffff; text-decoration: none; padding: 12px 24px; border-radius: 8px; font-weight: 700; display: inline-block;">
              Responder Encuesta Ahora
            </a>
          </div>
          <p style="font-size: 12px; color: #64748b;">
            Si el botón no funciona, copia y pega el siguiente enlace en tu navegador:<br/>
            <a href="{survey_url}" style="color: #00857c;">{survey_url}</a>
          </p>
        </div>
      </body>
    </html>
    """

    plain_body = (
        f"Hola {evaluator_name},\n\n"
        f"Te invitamos a completar {target_desc_plain} dentro del proceso '{evaluation_title}'.\n"
        f"{custom_block_plain}"
        f"{expiration_plain}\n"
        f"Accede a tu encuesta en el siguiente enlace:\n{survey_url}\n\n"
        f"Saludos,\nEquipo RRHH 360"
    )

    return subject, plain_body, html_body


def send_email_notification(
    *,
    to_email: str,
    subject: str,
    plain_body: str,
    html_body: str,
    smtp_override: dict | None = None,
) -> tuple[bool, str]:
    cfg = smtp_override or {}
    host = cfg.get("smtp_host") or settings.smtp_host
    port = int(cfg.get("smtp_port") or settings.smtp_port or 587)
    user = cfg.get("smtp_user") or settings.smtp_user
    password = cfg.get("smtp_password") or settings.smtp_password
    from_email = cfg.get("smtp_from_email") or settings.smtp_from_email or user or "no-reply@rrhh360.com"
    from_name = cfg.get("smtp_from_name") or settings.smtp_from_name or "RRHH 360"
    use_tls = cfg.get("smtp_use_tls", settings.smtp_use_tls)

    if not host:
        return False, "SMTP no configurado (aviso registrado en plataforma)"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{from_name} <{from_email}>"
    msg["To"] = to_email

    msg.attach(MIMEText(plain_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        if port == 465:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(host, port, context=context, timeout=15) as server:
                if user and password:
                    server.login(user, password)
                server.sendmail(from_email, [to_email], msg.as_string())
        else:
            with smtplib.SMTP(host, port, timeout=15) as server:
                if use_tls:
                    context = ssl.create_default_context()
                    server.starttls(context=context)
                if user and password:
                    server.login(user, password)
                server.sendmail(from_email, [to_email], msg.as_string())
        return True, "Enviado por SMTP"
    except Exception as exc:
        return False, f"Error SMTP: {exc}"

