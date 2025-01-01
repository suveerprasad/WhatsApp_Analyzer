from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import time

def generate_pdf_report(df, stats, visualizations):
    # Create PDF filename with timestamp
    filename = f"whatsapp_analysis_{int(time.time())}.pdf"
    doc = SimpleDocTemplate(filename, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30
    )
    story.append(Paragraph("WhatsApp Chat Analysis Report", title_style))
    story.append(Spacer(1, 20))
    
    # Basic Statistics Section
    story.append(Paragraph("Basic Statistics", styles['Heading2']))
    basic_stats = stats['basic_stats']
    basic_stats_data = [
        ["Total Messages", str(basic_stats['total_messages'])],
        ["Total Users", str(basic_stats['total_users'])],
        ["Total Words", str(basic_stats['total_words'])],
        ["Media Shared", str(basic_stats['total_media'])],
        ["Links Shared", str(basic_stats['total_links'])],
        ["Missed Calls", str(basic_stats['missed_calls'])],
        ["Analysis Period", f"{basic_stats['start_date']} to {basic_stats['end_date']}"]
    ]
    basic_stats_table = Table(basic_stats_data, colWidths=[200, 300])
    basic_stats_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(basic_stats_table)
    story.append(Spacer(1, 20))
    
    # User Activity Visualization
    story.append(Paragraph("User Activity Analysis", styles['Heading2']))
    if 'User Activity' in visualizations:
        img = Image(visualizations['User Activity'], width=6*inch, height=4*inch)
        story.append(img)
    story.append(Spacer(1, 20))
    
    # Most Active Users
    story.append(Paragraph("Most Active Users", styles['Heading3']))
    most_active_data = [[user, count] for user, count in stats['user_stats']['most_active_users'].items()]
    most_active_table = Table([["User", "Messages"]] + most_active_data)
    most_active_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(most_active_table)
    story.append(Spacer(1, 20))
    
    # Time Analysis
    story.append(Paragraph("Time Analysis", styles['Heading2']))
    if 'Time Analysis' in visualizations:
        img = Image(visualizations['Time Analysis'], width=6*inch, height=4*inch)
        story.append(img)
    
    time_stats = [
        ["Busiest Month", stats['time_stats']['busiest_month']],
        ["Busiest Day", stats['time_stats']['busiest_day']],
        ["Busiest Hour", f"{stats['time_stats']['busiest_hour']}:00"]
    ]
    time_stats_table = Table(time_stats)
    time_stats_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ]))
    story.append(time_stats_table)
    story.append(Spacer(1, 20))
    
    # Word Cloud Analysis
    story.append(Paragraph("Word Cloud Analysis", styles['Heading2']))
    if 'Word Cloud' in visualizations:
        img = Image(visualizations['Word Cloud'], width=6*inch, height=4*inch)
        story.append(img)
    
    # Top Words Table
    story.append(Paragraph("Most Used Words", styles['Heading3']))
    top_words_data = [[word['words'], word['count']] for word in stats['content_stats']['top_words'][:10]]
    top_words_table = Table([["Word", "Count"]] + top_words_data)
    top_words_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ]))
    story.append(top_words_table)
    story.append(Spacer(1, 20))
    
    # Emoji Analysis
    story.append(Paragraph("Emoji Analysis", styles['Heading2']))
    if 'Emoji Distribution' in visualizations:
        img = Image(visualizations['Emoji Distribution'], width=6*inch, height=4*inch)
        story.append(img)
    
    # Daily Activity Heatmap
    story.append(Paragraph("Daily Activity Patterns", styles['Heading2']))
    if 'Daily Activity' in visualizations:
        img = Image(visualizations['Daily Activity'], width=6*inch, height=4*inch)
        story.append(img)
    
    # Message Statistics
    story.append(Paragraph("Message Statistics", styles['Heading2']))
    msg_stats = [
        ["Average Message Length", f"{stats['message_stats']['avg_message_length']:.2f} characters"],
        ["Longest Message", f"{stats['message_stats']['max_message_length']} characters"],
        ["Total Characters", f"{stats['message_stats']['total_characters']:,}"]
    ]
    msg_stats_table = Table(msg_stats)
    msg_stats_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, -1), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ]))
    story.append(msg_stats_table)
    
    # Build PDF
    doc.build(story)
    return filename