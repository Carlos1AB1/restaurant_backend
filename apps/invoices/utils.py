from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.lib import colors
from django.conf import settings
from django.utils import timezone
import os

# Definición de colores personalizados que coinciden con la paleta de la app
FOODIE_PRIMARY = colors.HexColor('#FF6B6B')  # Rojo primario
FOODIE_SECONDARY = colors.HexColor('#4ECDC4')  # Turquesa secundario
FOODIE_ACCENT = colors.HexColor('#FFD166')  # Amarillo acento
FOODIE_BG = colors.HexColor('#F9F7F3')  # Fondo claro
FOODIE_TEXT = colors.HexColor('#333333')  # Texto oscuro
FOODIE_OUTLINE = colors.black  # Color del borde


def generate_invoice_pdf(order):
    """Genera la factura en formato PDF para un pedido dado con estilo cartoon."""
    buffer = BytesIO()

    # Configuración del documento con margen extra para el "borde cartoon"
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2.5 * cm,
        leftMargin=2.5 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm
    )

    # Estilos personalizados que coinciden con la estética de la app
    styles = getSampleStyleSheet()

    # Estilo para título principal - estilo "cartoon"
    styles.add(ParagraphStyle(
        name='CartoonTitle',
        parent=styles['Heading1'],
        textColor=FOODIE_PRIMARY,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold',
        fontSize=24,
        spaceAfter=12
    ))

    # Estilo para subtítulos
    styles.add(ParagraphStyle(
        name='CartoonSubtitle',
        parent=styles['Heading2'],
        textColor=FOODIE_PRIMARY,
        fontName='Helvetica-Bold',
        fontSize=16,
        spaceAfter=6
    ))

    # Estilo para la cabecera del restaurante
    styles.add(ParagraphStyle(
        name='RestaurantHeader',
        parent=styles['Normal'],
        textColor=FOODIE_TEXT,
        alignment=TA_CENTER,
        fontSize=12
    ))

    # Estilo para el total
    styles.add(ParagraphStyle(
        name='Total',
        parent=styles['Heading2'],
        textColor=FOODIE_PRIMARY,
        alignment=TA_RIGHT,
        fontName='Helvetica-Bold',
        fontSize=16
    ))

    # Estilo para el pie de página
    styles.add(ParagraphStyle(
        name='CartoonFooter',
        parent=styles['Normal'],
        textColor=FOODIE_TEXT,
        alignment=TA_CENTER,
        fontSize=10,
        fontName='Helvetica-Oblique'
    ))

    story = []

    # --- BORDE ESTILO CARTOON ---
    # Este borde se dibujará directamente sobre el canvas antes de generar el contenido
    # Lo implementaremos con una función personalizada

    # --- Cabecera ---
    # Logo del restaurante (centrado)
    try:
        logo_path = os.path.join(settings.STATIC_ROOT, 'images/logo.png')  # Ajusta la ruta
        if os.path.exists(logo_path):
            logo = Image(logo_path, width=6 * cm, height=2.5 * cm)
            logo.hAlign = 'CENTER'
            story.append(logo)
            story.append(Spacer(1, 0.5 * cm))
    except Exception as e:
        print(f"Advertencia: No se pudo incluir el logo: {e}")

    # Información del restaurante con formato centrado
    restaurant_name = settings.RESTAURANT_NAME
    restaurant_address = settings.RESTAURANT_ADDRESS.replace('\n', '<br/>')

    header_text = f"""
    <b>{restaurant_name}</b><br/>
    {restaurant_address}<br/>
    """
    story.append(Paragraph(header_text, styles['RestaurantHeader']))
    story.append(Spacer(1, 0.8 * cm))

    # Título principal con estilo cartoon
    story.append(Paragraph("<b>FACTURA</b>", styles['CartoonTitle']))
    story.append(Spacer(1, 0.5 * cm))

    # --- Datos del Pedido y Cliente en una tabla con estilo mejorado ---
    customer_name = order.user.get_full_name() or order.user.email
    customer_email = order.user.email
    customer_phone = order.phone_number or getattr(order.user, 'phone_number', "N/A")
    customer_address = order.delivery_address.replace('\n', '<br/>')

    order_date = timezone.localtime(order.created_at).strftime('%d/%m/%Y %H:%M')

    # Tabla de información en un recuadro estilo cartoon
    info_data = [
        [Paragraph(f"<b>Nº Pedido:</b> {order.order_number}", styles['Normal']),
         Paragraph(f"<b>Fecha:</b> {order_date}", styles['Normal'])],
        [Paragraph(f"<b>Cliente:</b> {customer_name}", styles['Normal']),
         Paragraph(f"<b>Email:</b> {customer_email}", styles['Normal'])],
        [Paragraph(f"<b>Dirección Entrega:</b><br/>{customer_address}", styles['Normal']),
         Paragraph(f"<b>Teléfono:</b> {customer_phone}", styles['Normal'])],
    ]

    info_table = Table(info_data, colWidths=[9 * cm, 9 * cm])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 0), (-1, -1), FOODIE_BG),
        ('BOX', (0, 0), (-1, -1), 1.5, FOODIE_OUTLINE),  # Borde exterior grueso
        ('LINEBELOW', (0, 0), (-1, 0), 1, FOODIE_OUTLINE),  # Línea debajo de la primera fila
        ('LINEBELOW', (0, 1), (-1, 1), 1, FOODIE_OUTLINE),  # Línea debajo de la segunda fila
    ]))

    story.append(info_table)
    story.append(Spacer(1, 1 * cm))

    # --- Tabla de Items con estilo mejorado ---
    story.append(Paragraph("<b>Detalle del Pedido:</b>", styles['CartoonSubtitle']))
    story.append(Spacer(1, 0.5 * cm))

    # Datos de la tabla
    table_data = [['Producto', 'Cantidad', 'Precio Unit.', 'Subtotal']]
    for item in order.items.all():
        table_data.append([
            Paragraph(item.product_name, styles['Normal']),
            str(item.quantity),
            f"{item.price:.2f} €",
            f"{item.get_total_price():.2f} €"
        ])

    # Estilo mejorado de la tabla al estilo cartoon
    item_table = Table(table_data, colWidths=[9 * cm, 2.5 * cm, 3 * cm, 3.5 * cm])
    item_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), FOODIE_PRIMARY),  # Fondo de cabecera
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),  # Texto blanco en cabecera
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  # Centrar cabecera
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Cabecera en negrita
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),  # Padding inferior cabecera
        ('TOPPADDING', (0, 0), (-1, 0), 12),  # Padding superior cabecera
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),  # Fondo blanco para datos
        ('BOX', (0, 0), (-1, -1), 2, FOODIE_OUTLINE),  # Borde exterior grueso
        ('INNERGRID', (0, 0), (-1, -1), 1, FOODIE_OUTLINE),  # Rejilla interior
        ('ALIGN', (0, 1), (0, -1), 'LEFT'),  # Alinear nombres a la izquierda
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),  # Centrar cantidades
        ('ALIGN', (2, 1), (3, -1), 'RIGHT'),  # Alinear precios a la derecha
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Alineación vertical
        ('LEFTPADDING', (0, 1), (0, -1), 10),  # Padding izquierdo para nombres
        ('RIGHTPADDING', (2, 1), (3, -1), 10),  # Padding derecho para precios
        ('TOPPADDING', (0, 1), (-1, -1), 10),  # Padding superior filas
        ('BOTTOMPADDING', (0, 1), (-1, -1), 10),  # Padding inferior filas
    ]))
    story.append(item_table)
    story.append(Spacer(1, 1.5 * cm))

    # --- Total con estilo destacado ---
    total_text = f"TOTAL: {order.total_price:.2f} €"

    # Crear una tabla de una celda para el total con un fondo y borde estilo cartoon
    total_table = Table([[Paragraph(total_text, styles['Total'])]], colWidths=[18 * cm])
    total_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), FOODIE_ACCENT),  # Fondo amarillo acento
        ('BOX', (0, 0), (0, 0), 2, FOODIE_OUTLINE),  # Borde grueso
        ('TOPPADDING', (0, 0), (0, 0), 12),  # Padding superior
        ('BOTTOMPADDING', (0, 0), (0, 0), 12),  # Padding inferior
        ('RIGHTPADDING', (0, 0), (0, 0), 20),  # Padding derecho extra
    ]))
    story.append(total_table)
    story.append(Spacer(1, 1.5 * cm))

    # --- Pie de página ---
    footer_text = "¡Gracias por tu compra! Esperamos verte pronto de nuevo."
    story.append(Paragraph(footer_text, styles['CartoonFooter']))

    # Función para agregar el borde estilo cartoon al PDF
    def add_cartoon_border(canvas, doc):
        canvas.saveState()

        # Establecer el color y grosor del borde
        canvas.setStrokeColor(FOODIE_OUTLINE)
        canvas.setLineWidth(3)

        # Dimensiones de la página
        page_width, page_height = A4

        # Dibujar el borde con esquinas redondeadas
        canvas.roundRect(1 * cm, 1 * cm, page_width - 2 * cm, page_height - 2 * cm, 10 * mm)

        # Agregar una línea decorativa en el color principal (opcional)
        canvas.setStrokeColor(FOODIE_PRIMARY)
        canvas.setLineWidth(1.5)
        canvas.roundRect(1.5 * cm, 1.5 * cm, page_width - 3 * cm, page_height - 3 * cm, 8 * mm)

        # Opciones para agregar fondos de patrones o decoraciones adicionales
        # canvas.setFillColor(colors.lightgrey)
        # canvas.setFillColorRGB(0.95, 0.95, 0.95)  # Gris muy claro

        # Restaurar el estado
        canvas.restoreState()

    # Construir el PDF con el borde personalizado
    try:
        doc.build(story, onFirstPage=add_cartoon_border, onLaterPages=add_cartoon_border)
        pdf = buffer.getvalue()
        buffer.close()
        return pdf
    except Exception as e:
        print(f"Error al generar PDF de factura para pedido {order.order_number}: {e}")
        buffer.close()
        raise  # Relanzar la excepción