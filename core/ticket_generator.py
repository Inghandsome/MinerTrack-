import os
from reportlab.lib.pagesizes import mm
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
import datetime

class GeneradorTicket:
    def __init__(self):
        # Tamaño de ticket típico de 80mm de ancho x 200mm de alto
        self.ancho = 80 * mm
        self.alto = 200 * mm

    def generar_ticket(self, placas, material, bruto, tara, neto, fecha_str, operador=""):
        # Nombre del archivo temporal
        nombre_archivo = f"Ticket_{placas}_{datetime.datetime.now().strftime('%H%M%S')}.pdf"
        
        c = canvas.Canvas(nombre_archivo, pagesize=(self.ancho, self.alto))
        
        # Inicio del dibujo
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(self.ancho / 2, self.alto - 15 * mm, "CORPORACIÓN ATSA")
        
        c.setFont("Helvetica", 10)
        c.drawCentredString(self.ancho / 2, self.alto - 22 * mm, "Báscula Camionera")
        c.drawCentredString(self.ancho / 2, self.alto - 27 * mm, "Ejido Carbonero Jacales")
        
        # Línea separadora
        c.setDash(3, 3)
        c.line(5 * mm, self.alto - 32 * mm, self.ancho - 5 * mm, self.alto - 32 * mm)
        c.setDash()  # Restaurar línea sólida
        
        # Datos del Movimiento
        c.setFont("Helvetica-Bold", 10)
        y = self.alto - 45 * mm
        c.drawString(5 * mm, y, "TICKET DE PESAJE")
        
        c.setFont("Helvetica", 10)
        y -= 8 * mm
        c.drawString(5 * mm, y, f"Fecha: {fecha_str}")
        y -= 6 * mm
        c.drawString(5 * mm, y, f"Placas: {placas}")
        y -= 6 * mm
        c.drawString(5 * mm, y, f"Material: {material}")
        
        # Línea separadora
        y -= 5 * mm
        c.setDash(3, 3)
        c.line(5 * mm, y, self.ancho - 5 * mm, y)
        c.setDash()
        
        # Pesos
        y -= 10 * mm
        c.setFont("Helvetica", 11)
        c.drawString(5 * mm, y, f"Peso Bruto:")
        c.drawRightString(self.ancho - 5 * mm, y, f"{bruto} kg")
        
        y -= 6 * mm
        c.drawString(5 * mm, y, f"Peso Tara:")
        c.drawRightString(self.ancho - 5 * mm, y, f"{tara} kg")
        
        y -= 8 * mm
        c.setFont("Helvetica-Bold", 12)
        c.drawString(5 * mm, y, f"PESO NETO:")
        c.drawRightString(self.ancho - 5 * mm, y, f"{neto} kg")
        
        # Operador en turno (Auditoría)
        if operador:
            y -= 10 * mm
            c.setDash(3, 3)
            c.line(5 * mm, y, self.ancho - 5 * mm, y)
            c.setDash()
            y -= 6 * mm
            c.setFont("Helvetica", 9)
            c.drawString(5 * mm, y, f"Atendido por: {operador}")

        # Pie de ticket
        y -= 15 * mm
        c.setFont("Helvetica", 8)
        c.drawCentredString(self.ancho / 2, y, "¡GRACIAS POR SU PREFERENCIA!")
        y -= 4 * mm
        c.drawCentredString(self.ancho / 2, y, "Sistema MinerTrack")
        
        c.save()
        return nombre_archivo
