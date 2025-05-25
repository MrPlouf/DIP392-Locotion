# This should be the full accounts/views.py file from the previous response where we fixed
# the logo path indentation and A4 import for ReportLab, and the TypeError in overview_view.
# I am providing it again here for completeness.

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Sum, Count
from django.db.models.functions import Coalesce, Cast, ExtractYear
from django.db.models.fields import CharField, IntegerField
from django.http import HttpResponse
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP
from collections import defaultdict, OrderedDict
from django.urls import reverse
import io
import os
import json
import traceback

# ReportLab Imports
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle, Spacer, SimpleDocTemplate, Image
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

from django.conf import settings

from .forms import (
    SignUpForm, UserUpdateForm, UserProfileUpdateForm,
    UserImageForm, DocumentForm, ManualTransactionForm
)
from .models import UserProfile, UserImage, Document, ManualTransaction


def home(request):
    return render(request, 'home.html')

def signup(request):
    if request.user.is_authenticated: return redirect('overview')
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid(): user = form.save(); login(request, user); messages.success(request, 'Account created! Welcome.'); return redirect('overview')
        else: messages.error(request, 'Please correct errors.')
    else: form = SignUpForm()
    return render(request, 'signup.html', {'form': form})

@login_required
def overview_view(request):
    user_profile = get_object_or_404(UserProfile, user=request.user); current_year = timezone.now().year
    overview_current_year = current_year
    num_years_for_chart = 3
    cy_doc_expenses = Document.objects.filter(user_profile=user_profile, year=current_year, amount_type='EXPENSE', amount__isnull=False).aggregate(total=Coalesce(Sum('amount'), Decimal('0.00')))['total']
    cy_doc_gains = Document.objects.filter(user_profile=user_profile, year=current_year, amount_type='GAIN', amount__isnull=False).aggregate(total=Coalesce(Sum('amount'), Decimal('0.00')))['total']
    cy_manual_expenses = ManualTransaction.objects.filter(user_profile=user_profile, date__year=current_year, amount_type='EXPENSE').aggregate(total=Coalesce(Sum('amount'), Decimal('0.00')))['total']
    cy_manual_gains = ManualTransaction.objects.filter(user_profile=user_profile, date__year=current_year, amount_type='GAIN').aggregate(total=Coalesce(Sum('amount'), Decimal('0.00')))['total']
    current_year_net_balance = (cy_doc_gains + cy_manual_gains) - (cy_doc_expenses + cy_manual_expenses)
    total_documents = Document.objects.filter(user_profile=user_profile).count()
    years_for_yoy = [current_year - i for i in range(num_years_for_chart - 1, -1, -1)]; yearly_gains_data = []; yearly_expenses_data = []
    for year_val in years_for_yoy:
        gains = (Document.objects.filter(user_profile=user_profile, year=year_val, amount_type='GAIN').aggregate(total=Coalesce(Sum('amount'), Decimal('0.00')))['total'] + ManualTransaction.objects.filter(user_profile=user_profile, date__year=year_val, amount_type='GAIN').aggregate(total=Coalesce(Sum('amount'), Decimal('0.00')))['total']); yearly_gains_data.append(float(gains))
        expenses = (Document.objects.filter(user_profile=user_profile, year=year_val, amount_type='EXPENSE').aggregate(total=Coalesce(Sum('amount'), Decimal('0.00')))['total'] + ManualTransaction.objects.filter(user_profile=user_profile, date__year=year_val, amount_type='EXPENSE').aggregate(total=Coalesce(Sum('amount'), Decimal('0.00')))['total']); yearly_expenses_data.append(float(expenses))
    yoy_chart_data = {'labels': [str(y) for y in years_for_yoy], 'gains': yearly_gains_data, 'expenses': yearly_expenses_data}
    category_spending = defaultdict(Decimal)
    doc_category_expenses = Document.objects.filter(user_profile=user_profile, year=current_year, amount_type='EXPENSE', amount__isnull=False).values('category').annotate(total_amount=Sum('amount'))
    for item in doc_category_expenses: category_display = dict(Document.CATEGORY_CHOICES).get(item['category'], item['category']); category_spending[category_display] += item.get('total_amount', Decimal('0.00'))
    manual_category_expenses = ManualTransaction.objects.filter(user_profile=user_profile, date__year=current_year, amount_type='EXPENSE').values('category').annotate(total_amount=Sum('amount'))
    for item in manual_category_expenses: category_display = dict(ManualTransaction.CATEGORY_CHOICES).get(item['category'], item['category']); category_spending[category_display] += item.get('total_amount', Decimal('0.00'))
    sorted_category_spending = OrderedDict(sorted(category_spending.items(), key=lambda item: item[1], reverse=True))
    category_chart_data = {'labels': list(sorted_category_spending.keys())[:7], 'data': [float(v) for v in list(sorted_category_spending.values())[:7]]}
    recent_activity_items = []
    recent_docs = Document.objects.filter(user_profile=user_profile, amount__isnull=False).exclude(amount_type='INFO').order_by('-uploaded_at')[:5]
    recent_manuals = ManualTransaction.objects.filter(user_profile=user_profile).order_by('-date')[:5]
    for doc in recent_docs: recent_activity_items.append({'date': doc.uploaded_at.date(), 'display_date': doc.uploaded_at, 'type': 'Document', 'description': doc.title, 'amount': doc.amount, 'amount_type': doc.amount_type})
    for man in recent_manuals: recent_activity_items.append({'date': man.date, 'display_date': man.date, 'type': 'Manual Entry', 'description': man.description, 'amount': man.amount, 'amount_type': man.amount_type})
    recent_activity_items.sort(key=lambda x: x['date'], reverse=True)
    context = {'page_title': 'Overview Dashboard', 'overview_current_year': overview_current_year, 'current_year_net_balance': current_year_net_balance, 'total_documents': total_documents, 'yoy_chart_data_json': json.dumps(yoy_chart_data), 'category_chart_data_json': json.dumps(category_chart_data), 'recent_activity': recent_activity_items[:5]}
    return render(request, 'accounts/overview.html', context)

@login_required
def profile_view(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    gallery_images = UserImage.objects.filter(user_profile=user_profile).order_by('-uploaded_at')
    image_upload_form = UserImageForm()
    context = {'page_title': 'My Profile', 'gallery_images': gallery_images, 'image_upload_form': image_upload_form}
    return render(request, 'accounts/profile.html', context)

@login_required
@transaction.atomic
def profile_edit_view(request):
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = UserProfileUpdateForm(request.POST, request.FILES, instance=user_profile)
        if user_form.is_valid() and profile_form.is_valid(): user_form.save(); profile_form.save(); messages.success(request, 'Profile updated!'); return redirect('profile')
        else: messages.error(request, 'Please correct errors.')
    else: user_form = UserUpdateForm(instance=request.user); profile_form = UserProfileUpdateForm(instance=user_profile)
    context = {'page_title': 'Edit Profile', 'user_form': user_form, 'profile_form': profile_form}
    return render(request, 'accounts/profile_edit.html', context)

@login_required
def add_user_image_view(request):
    user_profile = get_object_or_404(UserProfile, user=request.user)
    if request.method == 'POST':
        form = UserImageForm(request.POST, request.FILES)
        if form.is_valid(): user_image = form.save(commit=False); user_image.user_profile = user_profile; user_image.save(); messages.success(request, 'Image uploaded!'); return redirect('profile')
        else:
            messages.error(request, 'Error uploading image.')
            gallery_images = UserImage.objects.filter(user_profile=user_profile).order_by('-uploaded_at')
            context = {'page_title': 'My Profile', 'gallery_images': gallery_images, 'image_upload_form': form}
            return render(request, 'accounts/profile.html', context)
    return redirect('profile')

@login_required
def delete_user_image_view(request, image_id):
    user_profile = get_object_or_404(UserProfile, user=request.user)
    image_to_delete = get_object_or_404(UserImage, id=image_id, user_profile=user_profile)
    if request.method == 'POST': image_to_delete.delete(); messages.success(request, 'Image deleted.')
    else: messages.warning(request, 'Invalid request.')
    return redirect('profile')

@login_required
def documents_view(request):
    user_profile = get_object_or_404(UserProfile, user=request.user)
    doc_form_instance = DocumentForm(); show_modal_with_errors = False
    if request.method == 'POST': # This POST is for new document upload from the modal
        doc_form_instance = DocumentForm(request.POST, request.FILES)
        if doc_form_instance.is_valid():
            document = doc_form_instance.save(commit=False); document.user_profile = user_profile
            if not document.year: document.year = timezone.now().year
            document.save(); messages.success(request, f"Doc '{document.title}' uploaded!"); return redirect('documents')
        else: messages.error(request, "Error uploading. Check modal."); show_modal_with_errors = True
    
    documents_query = Document.objects.filter(user_profile=user_profile)
    selected_year_str = request.GET.get('year')
    if selected_year_str: documents_query = documents_query.filter(year=selected_year_str)
    if request.GET.get('category'): documents_query = documents_query.filter(category=request.GET.get('category'))
    if request.GET.get('amount_type'): documents_query = documents_query.filter(amount_type=request.GET.get('amount_type'))
    all_documents = documents_query.order_by('-year', '-uploaded_at')
    documents_by_year = defaultdict(list); [documents_by_year[doc.year or "Uncategorized"].append(doc) for doc in all_documents]
    sorted_documents_by_year = dict(sorted(documents_by_year.items(), key=lambda item: (isinstance(item[0], str), item[0]), reverse=True))
    distinct_years = Document.objects.filter(user_profile=user_profile).values_list('year', flat=True).distinct()
    available_years = sorted(list(set(y for y in distinct_years if y is not None) | {timezone.now().year}), reverse=True)
    context = {'page_title': 'My Documents', 'doc_form': doc_form_instance, 'show_modal_with_errors': show_modal_with_errors, 'documents_by_year': sorted_documents_by_year, 'available_years': available_years, 'category_choices': Document.CATEGORY_CHOICES, 'amount_type_choices': Document.AMOUNT_TYPE_CHOICES}
    return render(request, 'accounts/documents.html', context)

@login_required
def delete_document_view(request, doc_id):
    user_profile = get_object_or_404(UserProfile, user=request.user)
    document = get_object_or_404(Document, id=doc_id, user_profile=user_profile)
    if request.method == 'POST': doc_title = document.title; document.delete(); messages.success(request, f"Doc '{doc_title}' deleted.")
    else: messages.warning(request, "Invalid request.")
    return redirect('documents')

@login_required
def expenses_view(request):
    user_profile = get_object_or_404(UserProfile, user=request.user)
    manual_transaction_form_instance = ManualTransactionForm()
    current_year = timezone.now().year
    selected_year_str = request.GET.get('year', str(current_year))
    try: selected_year = int(selected_year_str)
    except ValueError: selected_year = current_year

    if request.method == 'POST' and 'submit_manual_transaction' in request.POST:
        manual_transaction_form_instance = ManualTransactionForm(request.POST)
        if manual_transaction_form_instance.is_valid():
            transaction_item = manual_transaction_form_instance.save(commit=False); transaction_item.user_profile = user_profile
            if not transaction_item.date: transaction_item.date = timezone.now().date()
            transaction_item.save(); messages.success(request, "Manual transaction added.")
            return redirect(f"{reverse('expenses')}?year={transaction_item.date.year}")
        else: messages.error(request, "Error adding manual transaction.")

    doc_expenses = Document.objects.filter(user_profile=user_profile, year=selected_year, amount_type='EXPENSE', amount__isnull=False).aggregate(total=Coalesce(Sum('amount'), Decimal('0.00')))['total']
    doc_gains = Document.objects.filter(user_profile=user_profile, year=selected_year, amount_type='GAIN', amount__isnull=False).aggregate(total=Coalesce(Sum('amount'), Decimal('0.00')))['total']
    manual_total_expenses = ManualTransaction.objects.filter(user_profile=user_profile, date__year=selected_year, amount_type='EXPENSE').aggregate(total=Coalesce(Sum('amount'), Decimal('0.00')))['total']
    manual_total_gains = ManualTransaction.objects.filter(user_profile=user_profile, date__year=selected_year, amount_type='GAIN').aggregate(total=Coalesce(Sum('amount'), Decimal('0.00')))['total']
    total_expenses_val = doc_expenses + manual_total_expenses
    total_gains_val = doc_gains + manual_total_gains
    net_balance_val = total_gains_val - total_expenses_val

    document_items = Document.objects.filter(user_profile=user_profile, year=selected_year, amount__isnull=False).exclude(amount_type='INFO').order_by('uploaded_at')
    manual_transaction_items = ManualTransaction.objects.filter(user_profile=user_profile, date__year=selected_year).order_by('date')
    
    doc_years_qs = Document.objects.filter(user_profile=user_profile).values_list('year', flat=True).distinct()
    manual_trans_years_qs = ManualTransaction.objects.filter(user_profile=user_profile).annotate(transaction_year=Cast(ExtractYear('date'), output_field=IntegerField())).values_list('transaction_year', flat=True).distinct()
    combined_years_int = set()
    for y_list in [doc_years_qs, manual_trans_years_qs]:
        for y_val in y_list:
            if y_val is not None: combined_years_int.add(int(y_val))
    combined_years_int.add(current_year)
    available_years = sorted(list(combined_years_int), reverse=True)
    
    context = {
        'page_title': f'Financial Summary for {selected_year}',
        'selected_year': selected_year,
        'current_year': current_year,
        'available_years': available_years,
        'total_expenses': total_expenses_val,
        'total_gains': total_gains_val,
        'net_balance': net_balance_val,
        'document_items': document_items,
        'manual_transaction_items': manual_transaction_items,
        'manual_transaction_form': manual_transaction_form_instance,
    }
    return render(request, 'accounts/expenses.html', context)

@login_required
def generate_expenses_pdf_view(request):
    user_profile = get_object_or_404(UserProfile, user=request.user)
    current_year = timezone.now().year
    selected_year_str = request.GET.get('year', str(current_year))
    try:
        selected_year = int(selected_year_str)
    except ValueError:
        selected_year = current_year

    doc_expenses = Document.objects.filter(user_profile=user_profile, year=selected_year, amount_type='EXPENSE', amount__isnull=False).aggregate(total=Coalesce(Sum('amount'), Decimal('0.00')))['total']
    doc_gains = Document.objects.filter(user_profile=user_profile, year=selected_year, amount_type='GAIN', amount__isnull=False).aggregate(total=Coalesce(Sum('amount'), Decimal('0.00')))['total']
    manual_total_expenses = ManualTransaction.objects.filter(user_profile=user_profile, date__year=selected_year, amount_type='EXPENSE').aggregate(total=Coalesce(Sum('amount'), Decimal('0.00')))['total']
    manual_total_gains = ManualTransaction.objects.filter(user_profile=user_profile, date__year=selected_year, amount_type='GAIN').aggregate(total=Coalesce(Sum('amount'), Decimal('0.00')))['total']
    total_expenses_val = doc_expenses + manual_total_expenses
    total_gains_val = doc_gains + manual_total_gains
    net_balance_val = total_gains_val - total_expenses_val

    combined_items = []
    doc_items_fin = Document.objects.filter(user_profile=user_profile, year=selected_year, amount__isnull=False).exclude(amount_type='INFO').order_by('uploaded_at')
    for item in doc_items_fin: combined_items.append({'date': item.uploaded_at.strftime("%Y-%m-%d") if item.uploaded_at else "N/A", 'description': item.title, 'category': item.get_category_display(), 'amount_type': item.amount_type, 'amount': item.amount if item.amount is not None else Decimal('0.00'), 'source': 'Document'})
    manual_items_fin = ManualTransaction.objects.filter(user_profile=user_profile, date__year=selected_year).order_by('date')
    for item in manual_items_fin: combined_items.append({'date': item.date.strftime("%Y-%m-%d"), 'description': item.description, 'category': item.get_category_display(), 'amount_type': item.amount_type, 'amount': item.amount if item.amount is not None else Decimal('0.00'), 'source': 'Manual Entry'})
    combined_items.sort(key=lambda x: x['date'])

    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                rightMargin=1.8*cm, leftMargin=1.8*cm,
                                topMargin=2*cm, bottomMargin=2.5*cm)
        styles = getSampleStyleSheet()
        story = []
        frame_width = doc.width
        
        user_display_name = request.user.get_full_name()
        if not user_display_name:
            user_display_name = request.user.username
            if "@" in user_display_name and "." in user_display_name and not (request.user.first_name or request.user.last_name):
                user_display_name = "Valued User"

        logo_path = None
        if hasattr(settings, 'STATICFILES_DIRS') and settings.STATICFILES_DIRS and isinstance(settings.STATICFILES_DIRS, (list, tuple)) and len(settings.STATICFILES_DIRS) > 0:
            possible_logo_path = os.path.join(settings.STATICFILES_DIRS[0], 'images', 'Frame.png')
            if os.path.exists(possible_logo_path): 
                logo_path = possible_logo_path
        
        if logo_path: 
            try:
                logo = Image(logo_path, width=2*cm, height=2*cm) 
                logo.hAlign = 'LEFT' 
                story.append(logo)
                story.append(Spacer(1, 0.2*cm)) 
            except Exception as img_e:
                print(f"Error loading logo image for PDF: {img_e}")
        
        title_style = ParagraphStyle('ReportTitle', parent=styles['h1'], alignment=TA_CENTER, fontSize=20, spaceBefore=0.5*cm if not logo_path else 0.2*cm, spaceAfter=0.3*cm, textColor=colors.HexColor("#1A237E"))
        story.append(Paragraph("Locotion Financial Report", title_style))
        
        sub_title_style = ParagraphStyle('SubTitle', parent=styles['h2'], alignment=TA_CENTER, fontSize=14, spaceAfter=0.7*cm, textColor=colors.HexColor("#424242"))
        story.append(Paragraph(f"Annual Summary for {selected_year}", sub_title_style))

        info_style = ParagraphStyle('UserInfo', parent=styles['Normal'], fontSize=9, spaceAfter=0.5*cm, alignment=TA_LEFT, leading=12)
        story.append(Paragraph(f"<b>Report For:</b> {user_display_name}", info_style))
        story.append(Paragraph(f"<b>Generated On:</b> {timezone.now().strftime('%B %d, %Y, %I:%M %p %Z')}", info_style))
        story.append(Spacer(1, 1*cm))

        story.append(Paragraph("<b>Financial Overview</b>", styles['h3']))
        summary_data = [
            [Paragraph("Total Gains:", styles['Normal']), Paragraph(f"${total_gains_val:.2f}", ParagraphStyle('Amount', parent=styles['Normal'], alignment=TA_RIGHT, textColor=colors.darkgreen))],
            [Paragraph("Total Expenses:", styles['Normal']), Paragraph(f"${total_expenses_val:.2f}", ParagraphStyle('Amount', parent=styles['Normal'], alignment=TA_RIGHT, textColor=colors.red))],
            [Paragraph("<b>Net Balance:</b>", ParagraphStyle('Bold', parent=styles['Normal'], fontName='Helvetica-Bold')), Paragraph(f"${net_balance_val:.2f}", ParagraphStyle('Amount', parent=styles['Normal'], alignment=TA_RIGHT, fontName='Helvetica-Bold', textColor=colors.darkblue if net_balance_val >= 0 else colors.darkred))]
        ]
        summary_table = Table(summary_data, colWidths=[frame_width*0.7, frame_width*0.28])
        summary_table.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.lightgrey), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('LEFTPADDING', (0,0), (-1,-1), 6), ('RIGHTPADDING', (0,0), (-1,-1), 6),
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#BDB48A")), ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor("#161219")), 
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'), ('FONTSIZE', (0,0), (-1,0), 10),
            ('BOTTOMPADDING', (0,0), (-1,0), 6), ('TOPPADDING', (0,0), (-1,0), 6),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 1.2*cm))

        if combined_items:
            story.append(Paragraph("<b>Itemized Entries</b>", styles['h3']))
            header_style_table = ParagraphStyle('THead',parent=styles['Normal'],fontName='Helvetica-Bold',fontSize=8, alignment=TA_LEFT)
            cell_style_table = ParagraphStyle('TCell',parent=styles['Normal'],fontSize=8, leading=10)
            amount_cell_style_table_right = ParagraphStyle('TCellAmount',parent=cell_style_table, alignment=TA_RIGHT)
            item_data = [[Paragraph(h, header_style_table) for h in ["Date", "Description", "Category", "Source", "Amount"]]]
            for item in combined_items:
                amount_val = item.get('amount', Decimal('0.00')); amount_type = item.get('amount_type', '');
                amount_str_prefix = '+' if amount_type == 'GAIN' else ('-' if amount_type == 'EXPENSE' else '');
                amount_str = f"{amount_str_prefix}${amount_val:.2f}";
                item_data.append([ Paragraph(str(item.get('date','')),cell_style_table), Paragraph(str(item.get('description','N/A'))[:70],cell_style_table), Paragraph(str(item.get('category','N/A')),cell_style_table), Paragraph(str(item.get('source','N/A')),cell_style_table), Paragraph(amount_str,amount_cell_style_table_right)])
            item_table_col_widths=[1.8*cm, 6.7*cm, 3*cm, 2.5*cm, 2*cm]; item_table = Table(item_data, colWidths=item_table_col_widths, repeatRows=1);
            item_table.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#DDDDDD")),('GRID', (0,0), (-1,-1), 0.25, colors.black),('VALIGN', (0,0), (-1,-1), 'TOP'), ('LEFTPADDING', (0,0),(-1,-1),3), ('RIGHTPADDING', (0,0),(-1,-1),3)])); story.append(item_table)

        def _draw_page_number(canvas, doc):
            canvas.saveState(); canvas.setFont('Helvetica', 9); canvas.setFillColor(colors.grey)
            page_num_text = f"Page {doc.page}"; canvas.drawRightString(doc.pagesize[0] - doc.rightMargin - 0.5*cm, doc.bottomMargin - 0.5*cm, page_num_text)
            canvas.drawString(doc.leftMargin + 0.5*cm, doc.bottomMargin - 0.5*cm, "Generated by Locotion"); canvas.restoreState()
        
        doc.build(story, onFirstPage=_draw_page_number, onLaterPages=_draw_page_number)
        pdf_value = buffer.getvalue(); buffer.close()
        response = HttpResponse(pdf_value, content_type='application/pdf')
        clean_username = "".join(c if c.isalnum() else "_" for c in user_display_name.replace(" ", "_"))
        filename = f'Locotion_Report_{selected_year}_{clean_username}.pdf'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response

    except Exception as e:
        print(f"!!! EXCEPTION during ReportLab PDF generation: {e} !!!")
        traceback.print_exc()
        messages.error(request, f"Could not generate PDF. An unexpected error occurred: {e}")
        expenses_url = reverse('expenses')
        return redirect(f"{expenses_url}?year={selected_year}")