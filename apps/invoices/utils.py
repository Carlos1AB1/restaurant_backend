from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.lib import colors
from django.conf import settings
from django.utils import timezone

def generate_invoice_pdf(order):
    """Genera la factura en formato PDF para un pedido dado."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story = []

    # --- Cabecera ---
    # Opcional: Logo del restaurante
    # try:
    #     logo_path = settings.STATICFILES_DIRS[0] + '/images/logo.png' # Ajusta la ruta a tu logo
    #     if os.path.exists(logo_path):
    #          logo = Image(logo_path, width=5*cm, height=2*cm) # Ajusta tamaño
    #          logo.hAlign = 'LEFT'
    #          story.append(logo)
    #          story.append(Spacer(1, 1*cm))
    # except:
    #     print("Advertencia: No se encontró el logo para la factura.")
    #     pass

    restaurant_name = settings.RESTAURANT_NAME
    restaurant_address = settings.RESTAURANT_ADDRESS.replace('\n', '<br/>') # Para saltos de línea en HTML

    header_text = f"""
    <b>{restaurant_name}</b><br/>
    {restaurant_address}<br/>
    """
    story.append(Paragraph(header_text, styles['Normal']))
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph(f"<b>FACTURA</b>", styles['h1']))
    story.append(Spacer(1, 0.2*cm))

    # --- Datos del Pedido y Cliente ---
    customer_name = order.user.get_full_name() or order.user.email
    customer_email = order.user.email
    customer_phone = order.phone_number or order.user.phone_number or "N/A"
    customer_address = order.delivery_address.replace('\n', '<br/>')

    order_date = timezone.localtime(order.created_at).strftime('%d/%m/%Y %H:%M')

    info_data = [
        [Paragraph(f"<b>Nº Pedido:</b> {order.order_number}", styles['Normal']), Paragraph(f"<b>Fecha:</b> {order_date}", styles['Normal'])],
        [Paragraph(f"<b>Cliente:</b> {customer_name}", styles['Normal']), Paragraph(f"<b>Email:</b> {customer_email}", styles['Normal'])],
        [Paragraph(f"<b>Dirección Entrega:</b><br/>{customer_address}", styles['Normal']), Paragraph(f"<b>Teléfono:</b> {customer_phone}", styles['Normal'])],
    ]
    info_table = Table(info_data, colWidths=[9*cm, 9*cm])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 1*cm))


    # --- Tabla de Items ---
    story.append(Paragraph("<b>Detalle del Pedido:</b>", styles['h3']))
    story.append(Spacer(1, 0.5*cm))

    table_data = [['Producto', 'Cantidad', 'Precio Unit.', 'Subtotal']]
    for item in order.items.all():
        table_data.append([
            Paragraph(item.product_name, styles['Normal']),
            str(item.quantity),
            f"{item.price:.2f} €",
            f"{item.get_total_price():.2f} €"
        ])

    # Estilo de la tabla
    item_table = Table(table_data, colWidths=[9*cm, 2*cm, 3*cm, 4*cm])
    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('ALIGN', (0, 1), (0, -1), 'LEFT'), # Alinear nombres a la izquierda
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 1), (0, -1), 5), # Padding izquierdo para nombres
        ('RIGHTPADDING', (1, 1), (-1, -1), 5),# Padding derecho para números
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'), # Alinear números a la derecha
    ]))
    story.append(item_table)
    story.append(Spacer(1, 1*cm))

    # --- Total ---
    total_text = f"<b>TOTAL: {order.total_price:.2f} €</b>"
    p_total = Paragraph(total_text, styles['h3'])
    p_total.alignment = TA_RIGHT
    story.append(p_total)
    story.append(Spacer(1, 1*cm))

    # --- Pie de página (opcional) ---
    footer_text = "Gracias por tu compra."
    story.append(Paragraph(footer_text, styles['Italic']))

    # Construir el PDF
    try:
        doc.build(story)
        pdf = buffer.getvalue()
        buffer.close()
        return pdf
    except Exception as e:
        print(f"Error al generar PDF de factura para pedido {order.order_number}: {e}")
        # Podrías devolver None o lanzar una excepción específica
        buffer.close()
        raise # Relanzar la excepción para que la señal sepa que falló