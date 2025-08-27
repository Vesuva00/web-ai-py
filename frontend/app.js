/**
 * 前端JavaScript应用
 * 处理用户交互、API调用和界面更新
 */

// 应用状态
let currentUser = null;
let accessToken = null;
let availableWorkflows = [];
let currentWorkflow = null;

// API基础URL
const API_BASE_URL = '/api';

// DOM加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

/**
 * 初始化应用
 */
function initializeApp() {
    // 检查是否已有有效的登录状态
    const savedToken = localStorage.getItem('access_token');
    const savedUser = localStorage.getItem('username');
    
    if (savedToken && savedUser) {
        accessToken = savedToken;
        currentUser = savedUser;
        
        // 验证token是否仍然有效
        validateToken().then(valid => {
            if (valid) {
                showMainSection();
            } else {
                showLoginSection();
            }
        });
    } else {
        showLoginSection();
    }
    
    // 设置选择框样式
    setupSelectStyles();
}

/**
 * 验证访问令牌
 */
async function validateToken() {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/me`, {
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });
        
        return response.ok;
    } catch (error) {
        console.error('Token验证失败:', error);
        return false;
    }
}

/**
 * 处理登录
 */
async function handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value.trim();
    const dailyCode = document.getElementById('daily-code').value.trim();
    const loginBtn = event.target.querySelector('button[type="submit"]');
    const loginText = document.getElementById('login-text');
    const loginSpinner = document.getElementById('login-spinner');
    const errorDiv = document.getElementById('login-error');
    
    if (!username || !dailyCode) {
        showError('请填写所有必需字段');
        return;
    }
    
    if (!/^\d{6}$/.test(dailyCode)) {
        showError('验证码必须是6位数字');
        return;
    }
    
    // 显示加载状态
    loginBtn.disabled = true;
    loginText.textContent = '登录中...';
    loginSpinner.classList.remove('hidden');
    errorDiv.classList.add('hidden');
    
    try {
        const response = await fetch(`${API_BASE_URL}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                username: username,
                daily_code: dailyCode
            })
        });
        
        const result = await response.json();
        
        if (response.ok) {
            // 登录成功
            accessToken = result.access_token;
            currentUser = result.username;
            
            // 保存到本地存储
            localStorage.setItem('access_token', accessToken);
            localStorage.setItem('username', currentUser);
            
            showToast('登录成功！', 'success');
            showMainSection();
        } else {
            // 登录失败
            showError(result.detail || '登录失败，请检查用户名和验证码');
        }
    } catch (error) {
        console.error('登录请求失败:', error);
        showError('网络错误，请稍后重试');
    } finally {
        // 恢复按钮状态
        loginBtn.disabled = false;
        loginText.textContent = '登录';
        loginSpinner.classList.add('hidden');
    }
}

/**
 * 显示错误信息
 */
function showError(message) {
    const errorDiv = document.getElementById('login-error');
    errorDiv.textContent = message;
    errorDiv.classList.remove('hidden');
}

/**
 * 显示登录界面
 */
function showLoginSection() {
    document.getElementById('login-section').classList.remove('hidden');
    document.getElementById('main-section').classList.add('hidden');
    document.getElementById('user-info').classList.add('hidden');
    
    // 清空表单
    document.getElementById('login-form').reset();
}

/**
 * 显示主界面
 */
async function showMainSection() {
    document.getElementById('login-section').classList.add('hidden');
    document.getElementById('main-section').classList.remove('hidden');
    document.getElementById('user-info').classList.remove('hidden');
    
    // 更新用户信息显示
    document.getElementById('username-display').textContent = `欢迎，${currentUser}`;
    
    // 加载工作流列表
    await loadWorkflows();
}

/**
 * 退出登录
 */
function logout() {
    // 清除本地存储
    localStorage.removeItem('access_token');
    localStorage.removeItem('username');
    
    // 重置状态
    accessToken = null;
    currentUser = null;
    availableWorkflows = [];
    currentWorkflow = null;
    
    // 关闭所有模态框
    closeWorkflowModal();
    
    showToast('已安全退出', 'info');
    showLoginSection();
}

/**
 * 加载工作流列表
 */
async function loadWorkflows() {
    try {
        const response = await fetch(`${API_BASE_URL}/workflows`, {
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });
        
        if (response.ok) {
            const result = await response.json();
            availableWorkflows = result.workflows;
            renderWorkflowCards();
        } else {
            showToast('加载工作流失败', 'error');
            renderEmptyWorkflows();
        }
    } catch (error) {
        console.error('加载工作流失败:', error);
        showToast('网络错误，无法加载工作流', 'error');
        renderEmptyWorkflows();
    }
}

/**
 * 渲染工作流卡片
 */
function renderWorkflowCards() {
    const container = document.getElementById('workflows-container');
    
    if (availableWorkflows.length === 0) {
        renderEmptyWorkflows();
        return;
    }
    
    container.innerHTML = '';
    
    availableWorkflows.forEach(workflow => {
        const card = createWorkflowCard(workflow);
        container.appendChild(card);
    });
}

/**
 * 渲染空工作流状态
 */
function renderEmptyWorkflows() {
    const container = document.getElementById('workflows-container');
    container.innerHTML = `
        <div class="col-span-full flex flex-col items-center justify-center py-12">
            <i class="fas fa-cogs text-gray-400 text-6xl mb-4 opacity-50"></i>
            <h3 class="text-xl text-gray-300 mb-2">暂无可用工作流</h3>
            <p class="text-gray-400">请联系管理员添加工作流</p>
        </div>
    `;
}

/**
 * 创建工作流卡片
 */
function createWorkflowCard(workflow) {
    const card = document.createElement('div');
    card.className = 'workflow-card glass-effect rounded-lg p-6 cursor-pointer';
    card.onclick = () => openWorkflow(workflow);
    
    const icon = getWorkflowIcon(workflow.name);
    const color = getWorkflowColor(workflow.name);
    const tags = getWorkflowTags(workflow);
    
    card.innerHTML = `
        <div class="text-center">
            <i class="${icon} ${color} text-4xl mb-4"></i>
            <h3 class="text-xl font-bold text-white mb-2">${workflow.description || workflow.name}</h3>
            <p class="text-gray-300 text-sm mb-4">${workflow.input_schema?.description || '点击开始使用'}</p>
            <div class="flex flex-wrap justify-center gap-2 text-xs">
                ${tags.map(tag => `<span class="${tag.class} px-2 py-1 rounded">${tag.text}</span>`).join('')}
            </div>
        </div>
    `;
    
    return card;
}

/**
 * 获取工作流图标
 */
function getWorkflowIcon(workflowName) {
    const iconMap = {
        'poem': 'fas fa-feather-alt',
        'image': 'fas fa-image',
        'text': 'fas fa-file-alt',
        'analysis': 'fas fa-chart-line',
        'translation': 'fas fa-language',
        'coding': 'fas fa-code',
        'default': 'fas fa-cogs'
    };
    
    for (const [key, icon] of Object.entries(iconMap)) {
        if (workflowName.toLowerCase().includes(key)) {
            return icon;
        }
    }
    
    return iconMap.default;
}

/**
 * 获取工作流颜色
 */
function getWorkflowColor(workflowName) {
    const colorMap = {
        'poem': 'text-yellow-400',
        'image': 'text-purple-400',
        'text': 'text-green-400',
        'analysis': 'text-blue-400',
        'translation': 'text-red-400',
        'coding': 'text-indigo-400',
        'default': 'text-gray-400'
    };
    
    for (const [key, color] of Object.entries(colorMap)) {
        if (workflowName.toLowerCase().includes(key)) {
            return color;
        }
    }
    
    return colorMap.default;
}

/**
 * 获取工作流标签
 */
function getWorkflowTags(workflow) {
    const tags = [];
    
    // 根据工作流名称添加标签
    if (workflow.name.includes('poem')) {
        tags.push({ text: '文本生成', class: 'bg-blue-500 text-white' });
        tags.push({ text: '创意写作', class: 'bg-green-500 text-white' });
    } else if (workflow.name.includes('image')) {
        tags.push({ text: '图像生成', class: 'bg-purple-500 text-white' });
        tags.push({ text: 'AI绘画', class: 'bg-pink-500 text-white' });
    } else {
        tags.push({ text: 'AI工作流', class: 'bg-gray-500 text-white' });
    }
    
    // 添加状态标签
    if (workflow.stats && workflow.stats.total_executions > 0) {
        tags.push({ 
            text: `${workflow.stats.total_executions}次使用`, 
            class: 'bg-blue-600 text-white' 
        });
    }
    
    return tags;
}

/**
 * 打开工作流
 */
function openWorkflow(workflow) {
    currentWorkflow = workflow;
    setupWorkflowModal(workflow);
    document.getElementById('workflow-modal').classList.remove('hidden');
    document.body.style.overflow = 'hidden';
}

/**
 * 关闭工作流模态框
 */
function closeWorkflowModal() {
    document.getElementById('workflow-modal').classList.add('hidden');
    document.body.style.overflow = 'auto';
    currentWorkflow = null;
}

/**
 * 设置工作流模态框
 */
function setupWorkflowModal(workflow) {
    // 设置标题和图标
    const icon = getWorkflowIcon(workflow.name);
    const color = getWorkflowColor(workflow.name);
    
    document.getElementById('workflow-modal-icon').className = `${icon} ${color}`;
    document.getElementById('workflow-modal-name').textContent = workflow.description || workflow.name;
    document.getElementById('workflow-description').textContent = workflow.input_schema?.description || '';
    
    // 渲染输入表单
    renderWorkflowForm(workflow.input_schema);
    
    // 重置结果显示
    document.getElementById('workflow-result').classList.add('hidden');
    document.getElementById('workflow-placeholder').classList.remove('hidden');
    
    // 重置表单
    document.getElementById('workflow-form').reset();
}

/**
 * JSON Schema表单渲染器
 */
function renderWorkflowForm(schema) {
    const container = document.getElementById('workflow-inputs-container');
    container.innerHTML = '';
    
    if (!schema || !schema.properties) {
        container.innerHTML = '<p class="text-gray-400">此工作流无需输入参数</p>';
        return;
    }
    
    const properties = schema.properties;
    const required = schema.required || [];
    
    Object.entries(properties).forEach(([fieldName, fieldSchema]) => {
        const fieldElement = createFormField(fieldName, fieldSchema, required.includes(fieldName));
        container.appendChild(fieldElement);
    });
}

/**
 * 创建表单字段
 */
function createFormField(name, schema, isRequired) {
    const fieldDiv = document.createElement('div');
    fieldDiv.className = 'mb-4';
    
    const label = document.createElement('label');
    label.className = 'block text-white text-sm font-medium mb-2';
    label.innerHTML = `
        <i class="${getFieldIcon(schema.type)} mr-1"></i>
        ${schema.description || name}
        ${isRequired ? ' *' : ''}
    `;
    
    let input;
    
    switch (schema.type) {
        case 'string':
            if (schema.enum) {
                input = createSelectField(name, schema);
            } else if (schema.format === 'textarea') {
                input = createTextareaField(name, schema, isRequired);
            } else {
                input = createTextInput(name, schema, isRequired);
            }
            break;
        case 'integer':
        case 'number':
            input = createNumberInput(name, schema, isRequired);
            break;
        case 'boolean':
            input = createCheckboxField(name, schema);
            break;
        case 'array':
            input = createArrayField(name, schema, isRequired);
            break;
        default:
            input = createTextInput(name, schema, isRequired);
    }
    
    fieldDiv.appendChild(label);
    fieldDiv.appendChild(input);
    
    return fieldDiv;
}

/**
 * 获取字段图标
 */
function getFieldIcon(type) {
    const iconMap = {
        'string': 'fas fa-font',
        'integer': 'fas fa-hashtag',
        'number': 'fas fa-calculator',
        'boolean': 'fas fa-toggle-on',
        'array': 'fas fa-list',
        'object': 'fas fa-cube'
    };
    
    return iconMap[type] || 'fas fa-edit';
}

/**
 * 创建文本输入框
 */
function createTextInput(name, schema, isRequired) {
    const input = document.createElement('input');
    input.type = 'text';
    input.id = `field-${name}`;
    input.name = name;
    input.required = isRequired;
    input.className = 'w-full px-4 py-3 rounded-lg bg-white bg-opacity-20 border border-gray-300 border-opacity-30 text-white placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-400';
    
    if (schema.default) input.value = schema.default;
    if (schema.placeholder) input.placeholder = schema.placeholder;
    if (schema.minLength) input.minLength = schema.minLength;
    if (schema.maxLength) input.maxLength = schema.maxLength;
    if (schema.pattern) input.pattern = schema.pattern;
    
    return input;
}

/**
 * 创建文本域
 */
function createTextareaField(name, schema, isRequired) {
    const textarea = document.createElement('textarea');
    textarea.id = `field-${name}`;
    textarea.name = name;
    textarea.required = isRequired;
    textarea.rows = 4;
    textarea.className = 'w-full px-4 py-3 rounded-lg bg-white bg-opacity-20 border border-gray-300 border-opacity-30 text-white placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-400';
    
    if (schema.default) textarea.value = schema.default;
    if (schema.placeholder) textarea.placeholder = schema.placeholder;
    if (schema.minLength) textarea.minLength = schema.minLength;
    if (schema.maxLength) textarea.maxLength = schema.maxLength;
    
    return textarea;
}

/**
 * 创建选择框
 */
function createSelectField(name, schema) {
    const select = document.createElement('select');
    select.id = `field-${name}`;
    select.name = name;
    select.className = 'w-full px-4 py-3 rounded-lg bg-white bg-opacity-20 border border-gray-300 border-opacity-30 text-white focus:outline-none focus:ring-2 focus:ring-blue-400';
    
    schema.enum.forEach(option => {
        const optionElement = document.createElement('option');
        optionElement.value = option;
        optionElement.textContent = option;
        if (schema.default === option) {
            optionElement.selected = true;
        }
        select.appendChild(optionElement);
    });
    
    return select;
}

/**
 * 创建数字输入框
 */
function createNumberInput(name, schema, isRequired) {
    const input = document.createElement('input');
    input.type = schema.type === 'integer' ? 'number' : 'number';
    input.id = `field-${name}`;
    input.name = name;
    input.required = isRequired;
    input.className = 'w-full px-4 py-3 rounded-lg bg-white bg-opacity-20 border border-gray-300 border-opacity-30 text-white placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-400';
    
    if (schema.default !== undefined) input.value = schema.default;
    if (schema.minimum !== undefined) input.min = schema.minimum;
    if (schema.maximum !== undefined) input.max = schema.maximum;
    if (schema.type === 'integer') input.step = 1;
    
    return input;
}

/**
 * 创建复选框
 */
function createCheckboxField(name, schema) {
    const wrapper = document.createElement('div');
    wrapper.className = 'flex items-center';
    
    const input = document.createElement('input');
    input.type = 'checkbox';
    input.id = `field-${name}`;
    input.name = name;
    input.className = 'mr-2 w-4 h-4 text-blue-600 rounded focus:ring-blue-500';
    
    if (schema.default) input.checked = schema.default;
    
    const label = document.createElement('label');
    label.htmlFor = `field-${name}`;
    label.className = 'text-white text-sm';
    label.textContent = schema.description || name;
    
    wrapper.appendChild(input);
    wrapper.appendChild(label);
    
    return wrapper;
}

/**
 * 创建数组字段
 */
function createArrayField(name, schema, isRequired) {
    const wrapper = document.createElement('div');
    
    const input = document.createElement('textarea');
    input.id = `field-${name}`;
    input.name = name;
    input.required = isRequired;
    input.rows = 3;
    input.className = 'w-full px-4 py-3 rounded-lg bg-white bg-opacity-20 border border-gray-300 border-opacity-30 text-white placeholder-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-400';
    input.placeholder = '请输入数组项，每行一个';
    
    const help = document.createElement('small');
    help.className = 'text-gray-400 text-xs mt-1 block';
    help.textContent = '每行输入一个数组项';
    
    wrapper.appendChild(input);
    wrapper.appendChild(help);
    
    return wrapper;
}

/**
 * 执行工作流
 */
async function executeWorkflow(event) {
    event.preventDefault();
    
    if (!currentWorkflow) {
        showToast('未选择工作流', 'error');
        return;
    }
    
    // 收集表单数据
    const inputs = collectFormData();
    
    // 验证必填字段
    if (!validateInputs(inputs)) {
        return;
    }
    
    const executeBtn = document.getElementById('workflow-execute-btn');
    const executeText = document.getElementById('workflow-execute-text');
    const executeSpinner = document.getElementById('workflow-execute-spinner');
    
    // 显示加载状态
    executeBtn.disabled = true;
    executeText.textContent = '执行中...';
    executeSpinner.classList.remove('hidden');
    
    // 隐藏之前的结果
    document.getElementById('workflow-result').classList.add('hidden');
    document.getElementById('workflow-placeholder').classList.add('hidden');
    
    try {
        const response = await fetch(`${API_BASE_URL}/workflows/execute`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${accessToken}`
            },
            body: JSON.stringify({
                workflow_type: currentWorkflow.name,
                inputs: inputs
            })
        });
        
        const result = await response.json();
        
        if (response.ok && result.success) {
            // 显示执行结果
            displayWorkflowResult(result.result);
            showToast('工作流执行成功！', 'success');
        } else {
            showToast(result.detail || '工作流执行失败', 'error');
            document.getElementById('workflow-placeholder').classList.remove('hidden');
        }
    } catch (error) {
        console.error('工作流执行请求失败:', error);
        showToast('网络错误，请稍后重试', 'error');
        document.getElementById('workflow-placeholder').classList.remove('hidden');
    } finally {
        // 恢复按钮状态
        executeBtn.disabled = false;
        executeText.textContent = '执行工作流';
        executeSpinner.classList.add('hidden');
    }
}

/**
 * 收集表单数据
 */
function collectFormData() {
    const form = document.getElementById('workflow-form');
    const formData = new FormData(form);
    const inputs = {};
    
    for (const [key, value] of formData.entries()) {
        const field = document.getElementById(`field-${key}`);
        
        if (field.type === 'checkbox') {
            inputs[key] = field.checked;
        } else if (field.type === 'number') {
            inputs[key] = field.valueAsNumber;
        } else if (field.tagName === 'TEXTAREA' && key.includes('array')) {
            // 处理数组字段
            inputs[key] = value.split('\n').filter(item => item.trim());
        } else {
            inputs[key] = value;
        }
    }
    
    return inputs;
}

/**
 * 验证输入数据
 */
function validateInputs(inputs) {
    if (!currentWorkflow.input_schema) return true;
    
    const required = currentWorkflow.input_schema.required || [];
    
    for (const field of required) {
        if (!inputs[field] || (typeof inputs[field] === 'string' && !inputs[field].trim())) {
            showToast(`请填写必填字段：${field}`, 'error');
            return false;
        }
    }
    
    return true;
}

/**
 * 显示工作流结果
 */
function displayWorkflowResult(result) {
    const outputs = result.outputs;
    const resultContainer = document.getElementById('workflow-result');
    
    resultContainer.innerHTML = '';
    
    // 根据输出结构动态渲染
    if (typeof outputs === 'object' && outputs !== null) {
        const resultCard = createResultCard(outputs);
        resultContainer.appendChild(resultCard);
    } else {
        const simpleResult = document.createElement('div');
        simpleResult.className = 'glass-effect rounded-lg p-6';
        simpleResult.innerHTML = `
            <h4 class="text-lg font-semibold text-white mb-4">执行结果</h4>
            <pre class="text-gray-300 whitespace-pre-wrap">${JSON.stringify(outputs, null, 2)}</pre>
        `;
        resultContainer.appendChild(simpleResult);
    }
    
    // 显示结果区域
    resultContainer.classList.remove('hidden');
}

/**
 * 创建结果卡片
 */
function createResultCard(outputs) {
    const card = document.createElement('div');
    card.className = 'glass-effect rounded-lg p-6';
    
    let content = '';
    
    // 特殊处理诗歌结果
    if (outputs.poem && outputs.title) {
        content = `
            <h4 class="text-xl font-bold text-center text-yellow-400 mb-4">${outputs.title}</h4>
            <div class="poem-display text-white text-center mb-4">${outputs.poem}</div>
            ${outputs.analysis ? `
                <div class="border-t border-gray-400 pt-4">
                    <h5 class="text-sm font-semibold text-gray-300 mb-2">创作说明：</h5>
                    <p class="text-sm text-gray-300">${outputs.analysis}</p>
                </div>
            ` : ''}
            ${outputs.metadata ? `
                <div class="mt-4 flex justify-between text-xs text-gray-400">
                    <span>${outputs.metadata.line_count || 0}行 · ${outputs.metadata.word_count || 0}字 · ${outputs.metadata.style || ''}风格</span>
                    <button onclick="copyResult('${outputs.title}', '${outputs.poem}')" class="bg-gray-600 hover:bg-gray-700 px-3 py-1 rounded transition">
                        <i class="fas fa-copy mr-1"></i>复制
                    </button>
                </div>
            ` : ''}
        `;
    } else {
        // 通用结果显示
        content = '<h4 class="text-lg font-semibold text-white mb-4">执行结果</h4>';
        
        Object.entries(outputs).forEach(([key, value]) => {
            content += `
                <div class="mb-3">
                    <label class="text-sm font-medium text-gray-300">${key}:</label>
                    <div class="mt-1 text-white">
                        ${typeof value === 'string' && value.includes('\n') ? 
                            `<pre class="whitespace-pre-wrap bg-black bg-opacity-20 p-3 rounded">${value}</pre>` :
                            `<span>${value}</span>`
                        }
                    </div>
                </div>
            `;
        });
        
        content += `
            <div class="mt-4 text-right">
                <button onclick="copyResult('结果', '${JSON.stringify(outputs).replace(/'/g, "\\'")}')" class="bg-gray-600 hover:bg-gray-700 px-3 py-1 rounded transition text-xs">
                    <i class="fas fa-copy mr-1"></i>复制结果
                </button>
            </div>
        `;
    }
    
    card.innerHTML = content;
    return card;
}

/**
 * 复制结果
 */
async function copyResult(title, content) {
    const fullText = `${title}\n\n${content}`;
    
    try {
        await navigator.clipboard.writeText(fullText);
        showToast('内容已复制到剪贴板', 'success');
    } catch (error) {
        console.error('复制失败:', error);
        
        // 降级到使用传统方法
        const textArea = document.createElement('textarea');
        textArea.value = fullText;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        
        showToast('内容已复制到剪贴板', 'success');
    }
}

/**
 * 显示Toast通知
 */
function showToast(message, type = 'info') {
    const toast = document.getElementById('toast');
    const icon = document.getElementById('toast-icon');
    const messageEl = document.getElementById('toast-message');
    
    // 设置图标和样式
    icon.className = '';
    toast.className = 'fixed top-4 right-4 glass-effect px-6 py-3 rounded-lg shadow-lg transform transition-transform duration-300 z-50';
    
    switch (type) {
        case 'success':
            icon.className = 'fas fa-check-circle text-green-400';
            toast.classList.add('text-green-100');
            break;
        case 'error':
            icon.className = 'fas fa-exclamation-circle text-red-400';
            toast.classList.add('text-red-100');
            break;
        case 'warning':
            icon.className = 'fas fa-exclamation-triangle text-yellow-400';
            toast.classList.add('text-yellow-100');
            break;
        default:
            icon.className = 'fas fa-info-circle text-blue-400';
            toast.classList.add('text-blue-100');
    }
    
    messageEl.textContent = message;
    
    // 显示Toast
    toast.classList.remove('translate-x-full');
    
    // 3秒后自动隐藏
    setTimeout(() => {
        toast.classList.add('translate-x-full');
    }, 3000);
}

/**
 * 设置选择框样式
 */
function setupSelectStyles() {
    const selects = document.querySelectorAll('select');
    selects.forEach(select => {
        // 为选择框添加自定义样式
        select.addEventListener('focus', function() {
            this.style.color = 'white';
        });
        
        select.addEventListener('change', function() {
            this.style.color = 'white';
        });
    });
}

// 全局错误处理
window.addEventListener('error', function(event) {
    console.error('全局错误:', event.error);
    showToast('发生未知错误，请刷新页面重试', 'error');
});

// 网络错误处理
window.addEventListener('unhandledrejection', function(event) {
    console.error('未处理的Promise错误:', event.reason);
    showToast('网络请求失败，请检查网络连接', 'error');
});

// 快捷键支持
document.addEventListener('keydown', function(event) {
    // ESC键关闭模态框
    if (event.key === 'Escape') {
        closeWorkflowModal();
    }
    
    // Ctrl+Enter快速提交表单
    if (event.ctrlKey && event.key === 'Enter') {
        const activeModal = document.querySelector('.fixed:not(.hidden)');
        if (activeModal) {
            const form = activeModal.querySelector('form');
            if (form) {
                form.requestSubmit();
            }
        }
    }
});

// 页面可见性变化处理
document.addEventListener('visibilitychange', function() {
    if (document.visibilityState === 'visible' && accessToken) {
        // 页面重新可见时验证token
        validateToken().then(valid => {
            if (!valid) {
                showToast('登录已过期，请重新登录', 'warning');
                logout();
            }
        });
    }
});
