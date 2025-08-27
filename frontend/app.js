// AI工作流系统前端应用
class AIWorkflowApp {
    constructor() {
        this.apiBase = 'http://127.0.0.1:5000/api';
        this.token = localStorage.getItem('access_token');
        this.user = JSON.parse(localStorage.getItem('user') || 'null');
        this.currentPage = 'workflows';
        
        this.init();
    }
    
    init() {
        this.initParticles();
        this.bindEvents();
        
        if (this.token && this.user) {
            this.showMainApp();
        } else {
            this.showLoginPage();
        }
    }
    
    initParticles() {
        particlesJS('particles-js', {
            particles: {
                number: { value: 80, density: { enable: true, value_area: 800 } },
                color: { value: '#ffffff' },
                shape: { type: 'circle' },
                opacity: { value: 0.5, random: false },
                size: { value: 3, random: true },
                line_linked: {
                    enable: true,
                    distance: 150,
                    color: '#ffffff',
                    opacity: 0.4,
                    width: 1
                },
                move: {
                    enable: true,
                    speed: 6,
                    direction: 'none',
                    random: false,
                    straight: false,
                    out_mode: 'out',
                    bounce: false
                }
            },
            interactivity: {
                detect_on: 'canvas',
                events: {
                    onhover: { enable: true, mode: 'repulse' },
                    onclick: { enable: true, mode: 'push' },
                    resize: true
                }
            },
            retina_detect: true
        });
    }
    
    bindEvents() {
        // 登录表单
        document.getElementById('loginFormElement').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleLogin();
        });
        
        // 注册表单
        document.getElementById('registerFormElement').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleRegister();
        });
        
        // 切换登录/注册
        document.getElementById('showRegister').addEventListener('click', (e) => {
            e.preventDefault();
            this.showRegisterForm();
        });
        
        document.getElementById('showLogin').addEventListener('click', (e) => {
            e.preventDefault();
            this.showLoginForm();
        });
        
        // 导航
        document.querySelectorAll('.nav-link[data-page]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = e.target.closest('.nav-link').dataset.page;
                this.switchPage(page);
            });
        });
        
        // 退出登录
        document.getElementById('logoutBtn').addEventListener('click', (e) => {
            e.preventDefault();
            this.logout();
        });
        
        // 工作流执行
        document.getElementById('executeBtn').addEventListener('click', () => {
            this.executeWorkflow();
        });
        
        document.getElementById('backToWorkflows').addEventListener('click', () => {
            this.showWorkflowsList();
        });
    }
    
    async handleLogin() {
        const form = document.getElementById('loginFormElement');
        const btn = form.querySelector('button[type="submit"]');
        const btnText = btn.querySelector('.btn-text');
        const loading = btn.querySelector('.loading');
        
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const dailyCode = document.getElementById('dailyCode').value;
        
        this.setLoading(btn, btnText, loading, true);
        
        try {
            const response = await fetch(`${this.apiBase}/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    username,
                    password,
                    daily_code: dailyCode
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.token = data.access_token;
                this.user = data.user;
                
                localStorage.setItem('access_token', this.token);
                localStorage.setItem('user', JSON.stringify(this.user));
                
                this.showAlert('success', '登录成功！');
                
                setTimeout(() => {
                    this.showMainApp();
                }, 1000);
            } else {
                this.showAlert('danger', data.error || '登录失败');
            }
        } catch (error) {
            this.showAlert('danger', '网络错误，请稍后重试');
        } finally {
            this.setLoading(btn, btnText, loading, false);
        }
    }
    
    async handleRegister() {
        const form = document.getElementById('registerFormElement');
        const btn = form.querySelector('button[type="submit"]');
        const btnText = btn.querySelector('.btn-text');
        const loading = btn.querySelector('.loading');
        
        const username = document.getElementById('regUsername').value;
        const email = document.getElementById('regEmail').value;
        const password = document.getElementById('regPassword').value;
        
        this.setLoading(btn, btnText, loading, true);
        
        try {
            const response = await fetch(`${this.apiBase}/auth/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    username,
                    email,
                    password
                })
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.showAlert('success', '注册成功！请登录');
                setTimeout(() => {
                    this.showLoginForm();
                }, 1500);
            } else {
                this.showAlert('danger', data.error || '注册失败');
            }
        } catch (error) {
            this.showAlert('danger', '网络错误，请稍后重试');
        } finally {
            this.setLoading(btn, btnText, loading, false);
        }
    }
    
    showLoginForm() {
        document.getElementById('loginForm').classList.remove('d-none');
        document.getElementById('registerForm').classList.add('d-none');
        this.clearAlert();
    }
    
    showRegisterForm() {
        document.getElementById('loginForm').classList.add('d-none');
        document.getElementById('registerForm').classList.remove('d-none');
        this.clearAlert();
    }
    
    showLoginPage() {
        document.getElementById('loginPage').classList.remove('d-none');
        document.getElementById('mainApp').classList.add('d-none');
    }
    
    showMainApp() {
        document.getElementById('loginPage').classList.add('d-none');
        document.getElementById('mainApp').classList.remove('d-none');
        
        // 显示用户信息
        document.getElementById('userDisplayName').textContent = this.user.username;
        document.getElementById('userEmail').textContent = this.user.email;
        
        // 加载工作流
        this.loadWorkflows();
    }
    
    switchPage(page) {
        // 更新导航
        document.querySelectorAll('.nav-link[data-page]').forEach(link => {
            link.classList.remove('active');
        });
        document.querySelector(`[data-page="${page}"]`).classList.add('active');
        
        // 显示对应页面
        document.getElementById('workflowsPage').classList.toggle('d-none', page !== 'workflows');
        document.getElementById('historyPage').classList.toggle('d-none', page !== 'history');
        
        this.currentPage = page;
        
        if (page === 'workflows') {
            this.loadWorkflows();
        } else if (page === 'history') {
            this.loadHistory();
        }
    }
    
    async loadWorkflows() {
        try {
            const response = await fetch(`${this.apiBase}/workflows/list`, {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.renderWorkflows(data.workflows);
            } else {
                this.showAlert('danger', data.error || '加载工作流失败');
            }
        } catch (error) {
            this.showAlert('danger', '网络错误，请稍后重试');
        }
    }
    
    renderWorkflows(workflows) {
        const container = document.getElementById('workflowCards');
        
        const workflowConfigs = {
            poetry_generator: {
                title: '诗歌生成器',
                description: '基于主题生成优美的诗歌',
                icon: 'fas fa-feather-alt',
                color: 'primary'
            },
            text_summary: {
                title: '文本摘要',
                description: '智能提取文本核心信息',
                icon: 'fas fa-compress-alt',
                color: 'success'
            }
        };
        
        container.innerHTML = workflows.map(workflow => {
            const config = workflowConfigs[workflow.type] || {
                title: workflow.name,
                description: workflow.description,
                icon: 'fas fa-cog',
                color: 'secondary'
            };
            
            return `
                <div class="col-md-6 col-lg-4 mb-4">
                    <div class="card workflow-card h-100" data-workflow="${workflow.type}">
                        <div class="card-body text-center">
                            <i class="${config.icon} fa-3x text-${config.color} mb-3"></i>
                            <h5 class="card-title">${config.title}</h5>
                            <p class="card-text text-muted">${config.description}</p>
                            <button class="btn btn-${config.color} btn-sm" onclick="app.selectWorkflow('${workflow.type}')">
                                <i class="fas fa-play me-1"></i>开始使用
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
    }
    
    selectWorkflow(workflowType) {
        this.currentWorkflow = workflowType;
        this.showWorkflowExecution(workflowType);
    }
    
    showWorkflowExecution(workflowType) {
        const workflowConfigs = {
            poetry_generator: {
                title: '诗歌生成器',
                inputs: [
                    {
                        name: 'theme',
                        label: '诗歌主题',
                        type: 'text',
                        placeholder: '请输入诗歌主题，如：春天、思乡、友情等',
                        required: true
                    },
                    {
                        name: 'style',
                        label: '诗歌风格',
                        type: 'select',
                        options: [
                            { value: '现代诗', text: '现代诗' },
                            { value: '古诗', text: '古诗' },
                            { value: '律诗', text: '律诗' },
                            { value: '词', text: '词' }
                        ],
                        value: '现代诗'
                    }
                ]
            },
            text_summary: {
                title: '文本摘要',
                inputs: [
                    {
                        name: 'text',
                        label: '原文本',
                        type: 'textarea',
                        placeholder: '请输入需要摘要的文本内容...',
                        required: true,
                        rows: 8
                    },
                    {
                        name: 'max_length',
                        label: '摘要最大长度',
                        type: 'number',
                        value: 200,
                        min: 50,
                        max: 500
                    }
                ]
            }
        };
        
        const config = workflowConfigs[workflowType];
        
        document.getElementById('currentWorkflowName').textContent = config.title;
        
        const inputsContainer = document.getElementById('workflowInputs');
        inputsContainer.innerHTML = config.inputs.map(input => {
            if (input.type === 'select') {
                return `
                    <div class="mb-3">
                        <label for="${input.name}" class="form-label">${input.label}</label>
                        <select class="form-control" id="${input.name}" name="${input.name}">
                            ${input.options.map(option => 
                                `<option value="${option.value}" ${option.value === input.value ? 'selected' : ''}>
                                    ${option.text}
                                </option>`
                            ).join('')}
                        </select>
                    </div>
                `;
            } else if (input.type === 'textarea') {
                return `
                    <div class="mb-3">
                        <label for="${input.name}" class="form-label">${input.label}</label>
                        <textarea class="form-control" id="${input.name}" name="${input.name}" 
                                  placeholder="${input.placeholder || ''}" 
                                  ${input.required ? 'required' : ''}
                                  rows="${input.rows || 3}"></textarea>
                    </div>
                `;
            } else {
                return `
                    <div class="mb-3">
                        <label for="${input.name}" class="form-label">${input.label}</label>
                        <input type="${input.type}" class="form-control" id="${input.name}" name="${input.name}"
                               placeholder="${input.placeholder || ''}" 
                               value="${input.value || ''}"
                               ${input.min ? `min="${input.min}"` : ''}
                               ${input.max ? `max="${input.max}"` : ''}
                               ${input.required ? 'required' : ''}>
                    </div>
                `;
            }
        }).join('');
        
        document.getElementById('workflowCards').classList.add('d-none');
        document.getElementById('workflowExecution').classList.remove('d-none');
        document.getElementById('workflowResult').classList.add('d-none');
    }
    
    showWorkflowsList() {
        document.getElementById('workflowCards').classList.remove('d-none');
        document.getElementById('workflowExecution').classList.add('d-none');
    }
    
    async executeWorkflow() {
        const btn = document.getElementById('executeBtn');
        const btnText = btn.querySelector('.btn-text');
        const loading = btn.querySelector('.loading');
        
        // 收集输入数据
        const inputs = {};
        const form = document.getElementById('workflowInputs');
        const formData = new FormData(form);
        
        form.querySelectorAll('input, select, textarea').forEach(input => {
            inputs[input.name] = input.value;
        });
        
        this.setLoading(btn, btnText, loading, true);
        
        try {
            const response = await fetch(`${this.apiBase}/workflows/execute`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.token}`
                },
                body: JSON.stringify({
                    workflow_type: this.currentWorkflow,
                    input_data: inputs
                })
            });
            
            const data = await response.json();
            
            if (response.ok && data.success) {
                this.showWorkflowResult(data.result, data.execution_time);
            } else {
                this.showAlert('danger', data.error || '执行失败');
            }
        } catch (error) {
            this.showAlert('danger', '网络错误，请稍后重试');
        } finally {
            this.setLoading(btn, btnText, loading, false);
        }
    }
    
    showWorkflowResult(result, executionTime) {
        const resultContainer = document.getElementById('workflowResult');
        
        let content = '';
        
        if (this.currentWorkflow === 'poetry_generator') {
            content = `
                <div class="alert alert-success">
                    <i class="fas fa-check-circle me-2"></i>诗歌生成成功
                </div>
                <div class="workflow-result">
${result.poetry}
                </div>
                <div class="mt-3">
                    <small class="text-muted">
                        <i class="fas fa-info-circle me-1"></i>
                        主题：${result.theme} | 风格：${result.style} | 
                        执行时间：${executionTime.toFixed(2)}秒 | 
                        Token使用：${result.tokens_used}
                    </small>
                </div>
            `;
        } else if (this.currentWorkflow === 'text_summary') {
            content = `
                <div class="alert alert-success">
                    <i class="fas fa-check-circle me-2"></i>文本摘要生成成功
                </div>
                <div class="workflow-result">
${result.summary}
                </div>
                <div class="mt-3">
                    <small class="text-muted">
                        <i class="fas fa-info-circle me-1"></i>
                        原文长度：${result.original_length}字 | 摘要长度：${result.summary_length}字 | 
                        执行时间：${executionTime.toFixed(2)}秒 | 
                        Token使用：${result.tokens_used}
                    </small>
                </div>
            `;
        }
        
        resultContainer.innerHTML = content;
        resultContainer.classList.remove('d-none');
        
        // 滚动到结果区域
        resultContainer.scrollIntoView({ behavior: 'smooth' });
    }
    
    async loadHistory(page = 1) {
        try {
            const response = await fetch(`${this.apiBase}/workflows/history?page=${page}&per_page=10`, {
                headers: {
                    'Authorization': `Bearer ${this.token}`
                }
            });
            
            const data = await response.json();
            
            if (response.ok) {
                this.renderHistory(data.calls, data.pagination);
            } else {
                this.showAlert('danger', data.error || '加载历史记录失败');
            }
        } catch (error) {
            this.showAlert('danger', '网络错误，请稍后重试');
        }
    }
    
    renderHistory(calls, pagination) {
        const container = document.getElementById('historyList');
        
        if (calls.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted py-5">
                    <i class="fas fa-history fa-3x mb-3"></i>
                    <p>暂无调用历史</p>
                </div>
            `;
            return;
        }
        
        container.innerHTML = calls.map(call => {
            const statusBadge = call.status === 'success' ? 'success' : 'danger';
            const statusText = call.status === 'success' ? '成功' : '失败';
            const workflowName = this.getWorkflowName(call.workflow_type);
            
            return `
                <div class="history-item">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h6 class="mb-1">${workflowName}</h6>
                            <p class="text-muted mb-1">
                                <i class="fas fa-clock me-1"></i>
                                ${new Date(call.created_at).toLocaleString('zh-CN')}
                            </p>
                            <p class="text-muted mb-0">
                                <i class="fas fa-stopwatch me-1"></i>
                                执行时间：${call.execution_time ? call.execution_time.toFixed(2) : '0'}秒
                                ${call.tokens_used ? ` | Token：${call.tokens_used}` : ''}
                            </p>
                            ${call.error_message ? `<p class="text-danger mb-0"><small>${call.error_message}</small></p>` : ''}
                        </div>
                        <span class="badge bg-${statusBadge}">${statusText}</span>
                    </div>
                </div>
            `;
        }).join('');
        
        // 渲染分页
        this.renderPagination(pagination);
    }
    
    renderPagination(pagination) {
        const container = document.getElementById('historyPagination');
        
        if (pagination.pages <= 1) {
            container.innerHTML = '';
            return;
        }
        
        let paginationHtml = '<nav><ul class="pagination">';
        
        // 上一页
        if (pagination.has_prev) {
            paginationHtml += `
                <li class="page-item">
                    <a class="page-link" href="#" onclick="app.loadHistory(${pagination.page - 1})">上一页</a>
                </li>
            `;
        }
        
        // 页码
        for (let i = 1; i <= pagination.pages; i++) {
            if (i === pagination.page) {
                paginationHtml += `<li class="page-item active"><span class="page-link">${i}</span></li>`;
            } else {
                paginationHtml += `
                    <li class="page-item">
                        <a class="page-link" href="#" onclick="app.loadHistory(${i})">${i}</a>
                    </li>
                `;
            }
        }
        
        // 下一页
        if (pagination.has_next) {
            paginationHtml += `
                <li class="page-item">
                    <a class="page-link" href="#" onclick="app.loadHistory(${pagination.page + 1})">下一页</a>
                </li>
            `;
        }
        
        paginationHtml += '</ul></nav>';
        container.innerHTML = paginationHtml;
    }
    
    getWorkflowName(workflowType) {
        const names = {
            poetry_generator: '诗歌生成器',
            text_summary: '文本摘要'
        };
        return names[workflowType] || workflowType;
    }
    
    logout() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user');
        this.token = null;
        this.user = null;
        this.showLoginPage();
    }
    
    setLoading(btn, btnText, loading, isLoading) {
        if (isLoading) {
            btn.disabled = true;
            btnText.classList.add('d-none');
            loading.classList.remove('d-none');
        } else {
            btn.disabled = false;
            btnText.classList.remove('d-none');
            loading.classList.add('d-none');
        }
    }
    
    showAlert(type, message) {
        const container = document.getElementById('alertContainer');
        container.innerHTML = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
    }
    
    clearAlert() {
        document.getElementById('alertContainer').innerHTML = '';
    }
}

// 初始化应用
const app = new AIWorkflowApp();
