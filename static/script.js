// انتظار تحميل الصفحة
document.addEventListener('DOMContentLoaded', function() {
    console.log('SmartStudy - تم تحميل الصفحة بنجاح');
    
    // إغلاق التنبيهات تلقائياً بعد 5 ثوان
    setTimeout(() => {
        document.querySelectorAll('.alert').forEach(alert => {
            try {
                let bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } catch (e) {
                console.log('خطأ في إغلاق التنبيه:', e);
            }
        });
    }, 5000);

    // استرجاع الوضع المحفوظ
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.body.className = savedTheme + '-mode';
    updateThemeIcon(savedTheme);

    // رسم بياني إذا كان موجوداً
    if (document.getElementById('gradesChart')) {
        setTimeout(() => drawGradesChart(), 100);
    }
    
    // تشغيل العداد اليومي
    startDailyTimer();
    
    // تهيئة المساعد الذكي
    initSmartAssistant();

    // أزرار التعديل
    document.querySelectorAll('.edit-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            const id = this.getAttribute('data-id');
            const name = this.getAttribute('data-name');
            const grade = this.getAttribute('data-grade');
            editSubject(id, name, grade);
        });
    });

    // تفعيل جميع تلميحات الأدوات
    try {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    } catch (e) {
        console.log('خطأ في تفعيل tooltips:', e);
    }

    // إضافة تأثيرات حركية للبطاقات
    document.querySelectorAll('.card').forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-5px)';
        });
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
});

// ========== تبديل الوضع النهاري/الليلي ==========
function toggleTheme() {
    let current = document.body.className;
    let newTheme = current.includes('light') ? 'dark' : 'light';
    document.body.className = newTheme + '-mode';
    localStorage.setItem('theme', newTheme);
    updateThemeIcon(newTheme);
    
    // عرض رسالة تأكيد
    showToast(`تم التبديل إلى الوضع ${newTheme === 'light' ? 'النهاري' : 'الليلي'}`);
}

function updateThemeIcon(theme) {
    const btn = document.getElementById('themeToggle');
    if (btn) {
        btn.innerHTML = theme === 'dark' ? '<i class="bi bi-sun"></i>' : '<i class="bi bi-moon-stars"></i>';
        btn.setAttribute('title', theme === 'dark' ? 'الوضع النهاري' : 'الوضع الليلي');
    }
}

// ========== رسم بياني للدرجات ==========
function drawGradesChart() {
    const ctx = document.getElementById('gradesChart').getContext('2d');
    
    // الحصول على القيم
    const excellent = parseInt(document.getElementById('excellentCount')?.textContent || 0);
    const veryGood = parseInt(document.getElementById('veryGoodCount')?.textContent || 0);
    const good = parseInt(document.getElementById('goodCount')?.textContent || 0);
    const pass = parseInt(document.getElementById('passCount')?.textContent || 0);
    const fail = parseInt(document.getElementById('failCount')?.textContent || 0);
    
    // التحقق من وجود بيانات
    if (excellent + veryGood + good + pass + fail === 0) {
        ctx.font = '16px Arial';
        ctx.fillStyle = '#999';
        ctx.textAlign = 'center';
        ctx.fillText('لا توجد بيانات كافية', ctx.canvas.width/2, ctx.canvas.height/2);
        return;
    }
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['ممتاز (90-100)', 'جيد جداً (80-89)', 'جيد (70-79)', 'مقبول (60-69)', 'ضعيف (<60)'],
            datasets: [{
                data: [excellent, veryGood, good, pass, fail],
                backgroundColor: ['#28a745', '#17a2b8', '#ffc107', '#fd7e14', '#dc3545'],
                borderWidth: 0,
                hoverOffset: 10
            }]
        },
        options: { 
            responsive: true, 
            maintainAspectRatio: true,
            plugins: { 
                legend: { 
                    position: 'bottom',
                    labels: {
                        font: {
                            family: 'Segoe UI',
                            size: 12
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.label || '';
                            let value = context.raw || 0;
                            let total = context.dataset.data.reduce((a, b) => a + b, 0);
                            let percentage = Math.round((value / total) * 100);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            },
            cutout: '60%'
        }
    });
}

// ========== عداد تنازلي يومي ==========
function startDailyTimer() {
    const timerElement = document.getElementById('dailyTimer');
    if (!timerElement) return;
    
    // حساب الوقت المتبقي حتى نهاية اليوم (افتراضي: ساعتان)
    let totalSeconds = 2 * 60 * 60;
    
    function updateTimer() {
        const hours = Math.floor(totalSeconds / 3600);
        const minutes = Math.floor((totalSeconds % 3600) / 60);
        const seconds = totalSeconds % 60;
        
        timerElement.textContent = `${hours.toString().padStart(2,'0')}:${minutes.toString().padStart(2,'0')}:${seconds.toString().padStart(2,'0')}`;
        
        if (totalSeconds > 0) {
            totalSeconds--;
        } else {
            // إعادة التعيين عند الوصول للصفر
            totalSeconds = 2 * 60 * 60;
            showToast('انتهى وقت الدراسة! لنبدأ جلسة جديدة');
        }
    }
    
    updateTimer();
    setInterval(updateTimer, 1000);
}

// ========== المساعد الذكي ==========
function initSmartAssistant() {
    if (!document.querySelector('.smart-assistant')) {
        const html = `
            <div class="smart-assistant" id="smartAssistant">
                <div class="assistant-header">
                    <span><i class="bi bi-robot"></i> المساعد الذكي</span>
                    <button class="assistant-close" onclick="toggleAssistant()" aria-label="إغلاق">&times;</button>
                </div>
                <div class="assistant-body" id="assistantBody">
                    <div class="text-center">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">جاري التحميل...</span>
                        </div>
                    </div>
                </div>
            </div>
            <button class="assistant-toggle" onclick="toggleAssistant()" data-bs-toggle="tooltip" title="المساعد الذكي">
                <i class="bi bi-chat-dots"></i>
            </button>
        `;
        document.body.insertAdjacentHTML('beforeend', html);
    }
    loadAssistantTips();
    
    // تشغيل النصائح كل 30 ثانية
    setInterval(loadAssistantTips, 30000);
}

function toggleAssistant() {
    const assistant = document.getElementById('smartAssistant');
    if (assistant) {
        if (assistant.style.display === 'none' || assistant.style.display === '') {
            assistant.style.display = 'block';
            // تحميل نصيحة جديدة عند الفتح
            loadAssistantTips();
        } else {
            assistant.style.display = 'none';
        }
    }
}

function loadAssistantTips() {
    const tips = [
        { text: "📚 خصص 25 دقيقة دراسة ثم 5 دقائق راحة (تقنية البومودورو)", icon: "🍅" },
        { text: "🎯 ركز على المواد التي درجاتها أقل من 60 أولاً", icon: "⚠️" },
        { text: "📝 راجع ملاحظاتك قبل النوم لترسيخ المعلومات", icon: "🌙" },
        { text: "💡 استخدم الخرائط الذهنية للمواد النظرية", icon: "🧠" },
        { text: "👥 ناقش ما تعلمته مع زملائك لتعميق الفهم", icon: "🤝" },
        { text: "🥗 لا تنس تناول وجبات صحية خلال يومك", icon: "🍎" },
        { text: "💤 النوم الكافي (7-8 ساعات) يحسن الذاكرة", icon: "😴" },
        { text: "🏃 خذ استراحة قصيرة للحركة كل ساعة", icon: "🚶" },
        { text: "📅 التزم بخطتك الأسبوعية ولا تؤجل مهام اليوم", icon: "📌" },
        { text: "🎉 كافئ نفسك بعد إنجاز المهام الصعبة", icon: "🏆" }
    ];
    
    const randomTip = tips[Math.floor(Math.random() * tips.length)];
    const assistantBody = document.getElementById('assistantBody');
    
    if (assistantBody) {
        assistantBody.innerHTML = `
            <div class="text-center mb-2" style="font-size: 2rem;">${randomTip.icon}</div>
            <p class="mb-0">${randomTip.text}</p>
        `;
    }
}

// ========== دالة التعديل ==========
function editSubject(id, name, grade) {
    document.getElementById('editSubjectName').value = name;
    document.getElementById('editGrade').value = grade;
    document.getElementById('editForm').action = '/edit_subject/' + id;
    
    // فتح المودال
    try {
        const modal = new bootstrap.Modal(document.getElementById('editSubjectModal'));
        modal.show();
    } catch (e) {
        console.log('خطأ في فتح المودال:', e);
    }
}

// ========== تأكيد الحذف ==========
function confirmDelete() {
    return confirm('⚠️ هل أنت متأكد من حذف هذه المادة؟ لا يمكن التراجع عن هذا الإجراء.');
}

// ========== عرض رسالة منبثقة ==========
function showToast(message, type = 'info') {
    // إنشاء عنصر toast إذا لم يكن موجوداً
    let toastContainer = document.querySelector('.toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '9999';
        document.body.appendChild(toastContainer);
    }
    
    const toastId = 'toast-' + Date.now();
    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center text-white bg-${type} border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    try {
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, { delay: 3000 });
        toast.show();
        
        // حذف العنصر بعد الاختفاء
        setTimeout(() => {
            toastElement.remove();
        }, 4000);
    } catch (e) {
        console.log('خطأ في عرض toast:', e);
    }
}

// ========== دالة تنسيق الأرقام ==========
function formatNumber(num, decimals = 1) {
    return Number(num).toFixed(decimals);
}

// ========== دالة البحث في الجدول ==========
function searchTable(inputId, tableId) {
    const input = document.getElementById(inputId);
    const filter = input.value.toLowerCase();
    const table = document.getElementById(tableId);
    const rows = table.getElementsByTagName('tr');
    
    for (let i = 1; i < rows.length; i++) {
        const cells = rows[i].getElementsByTagName('td');
        let found = false;
        
        for (let j = 0; j < cells.length - 1; j++) {
            const cell = cells[j];
            if (cell) {
                const textValue = cell.textContent || cell.innerText;
                if (textValue.toLowerCase().indexOf(filter) > -1) {
                    found = true;
                    break;
                }
            }
        }
        
        rows[i].style.display = found ? '' : 'none';
    }
}

// ========== تصدير البيانات إلى PDF ==========
function exportToPDF() {
    showToast('جاري تجهيز ملف PDF...', 'info');
    // يمكن إضافة مكتبة jsPDF هنا
}

// ========== مشاركة الخطة ==========
function sharePlan() {
    if (navigator.share) {
        navigator.share({
            title: 'خطتي الأسبوعية - SmartStudy',
            text: 'تفقد خطتي الأسبوعية الذكية على SmartStudy',
            url: window.location.href
        }).catch(console.error);
    } else {
        // نسخ الرابط للحافظة
        navigator.clipboard.writeText(window.location.href).then(() => {
            showToast('تم نسخ الرابط!', 'success');
        });
    }
}