// 全局变量
let isProcessing = false;
let currentStage = 0;
let processResults = {
    stage1: {},
    stage2: {},
    stage3: {}
};

// DOM元素
const apiUrlInput = document.getElementById('apiUrl');
const startBtn = document.getElementById('startBtn');
const retryBtn = document.getElementById('retryBtn');
const progressSection = document.getElementById('progressSection');
const resultSection = document.getElementById('resultSection');
const errorSection = document.getElementById('errorSection');
const logContainer = document.getElementById('logContainer');

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    startBtn.addEventListener('click', startProcess);
    retryBtn.addEventListener('click', resetAndRetry);
    
    // 回车键触发开始
    apiUrlInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && !isProcessing) {
            startProcess();
        }
    });
});

// 开始处理流程
async function startProcess() {
    const apiUrl = apiUrlInput.value.trim();
    
    if (!apiUrl) {
        alert('请输入API文档链接');
        return;
    }
    
    if (!isValidUrl(apiUrl)) {
        alert('请输入有效的URL地址');
        return;
    }
    
    isProcessing = true;
    currentStage = 0;
    
    // 更新UI状态
    updateButtonState(true);
    showProgressSection();
    hideResultSection();
    hideErrorSection();
    clearLogs();
    
    try {
        // 开始处理流程
        await processApiDocuments(apiUrl);
    } catch (error) {
        console.error('处理过程中出错:', error);
        showError(error.message || '处理过程中发生未知错误');
    } finally {
        isProcessing = false;
        updateButtonState(false);
    }
}

// 处理API文档的主流程
async function processApiDocuments(apiUrl) {
    addLog('开始处理API文档...', 'info');
    addLog(`目标URL: ${apiUrl}`, 'info');
    
    // 阶段1: 下载原始数据
    const stage1Result = await executeStage(1, '下载llms.txt和MD文件', async () => {
        const response = await fetch('/api/stage1', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: apiUrl })
        });
        
        if (!response.ok) {
            throw new Error(`阶段1失败: ${response.statusText}`);
        }
        
        const result = await response.json();
        addLog(`下载完成: ${result.downloaded_files} 个文件`, 'success');
        return result;
    });
    processResults.stage1 = stage1Result;
    
    // 阶段2: 数据清洗和转换
    const stage2Result = await executeStage(2, '清洗MD文件并转换为YAML', async () => {
        const response = await fetch('/api/stage2', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (!response.ok) {
            throw new Error(`阶段2失败: ${response.statusText}`);
        }
        
        const result = await response.json();
        addLog(`转换完成: ${result.processed_files} 个文件`, 'success');
        return result;
    });
    processResults.stage2 = stage2Result;
    
    // 阶段3: 最终合并
    const stage3Result = await executeStage(3, '合并所有YAML文件', async () => {
        const response = await fetch('/api/stage3', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (!response.ok) {
            throw new Error(`阶段3失败: ${response.statusText}`);
        }
        
        const result = await response.json();
        addLog(`合并完成: ${result.merged_files} 个分类文件`, 'success');
        return result;
    });
    processResults.stage3 = stage3Result;
    
    // 显示最终结果
    showResult();
    addLog('所有处理完成！', 'success');
}

// 执行单个阶段
async function executeStage(stageNum, description, asyncFunction) {
    currentStage = stageNum;
    
    // 更新阶段状态
    updateStageStatus(stageNum, 'active', '处理中...');
    addLog(`开始${description}...`, 'info');
    
    try {
        // 模拟进度更新
        updateStageProgress(stageNum, 10);
        
        const result = await asyncFunction();
        
        // 完成进度
        updateStageProgress(stageNum, 100);
        updateStageStatus(stageNum, 'completed', '完成');
        
        return result;
    } catch (error) {
        updateStageStatus(stageNum, 'error', '失败');
        addLog(`${description}失败: ${error.message}`, 'error');
        throw error;
    }
}

// 更新阶段状态
function updateStageStatus(stageNum, status, statusText) {
    const stage = document.getElementById(`stage${stageNum}`);
    const statusElement = stage.querySelector('.stage-status');
    
    // 移除所有状态类
    stage.classList.remove('active', 'completed', 'error');
    
    // 添加新状态类
    if (status !== 'waiting') {
        stage.classList.add(status);
    }
    
    statusElement.textContent = statusText;
}

// 更新阶段进度
function updateStageProgress(stageNum, percentage) {
    const stage = document.getElementById(`stage${stageNum}`);
    const progressFill = stage.querySelector('.progress-fill');
    progressFill.style.width = `${percentage}%`;
}

// 添加日志
function addLog(message, type = 'info') {
    const logEntry = document.createElement('div');
    logEntry.className = `log-entry ${type}`;
    logEntry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    
    logContainer.appendChild(logEntry);
    logContainer.scrollTop = logContainer.scrollHeight;
}

// 清空日志
function clearLogs() {
    logContainer.innerHTML = '<div class="log-entry">开始处理...</div>';
}

// 显示进度区域
function showProgressSection() {
    progressSection.style.display = 'block';
    
    // 重置所有阶段状态
    for (let i = 1; i <= 3; i++) {
        updateStageStatus(i, 'waiting', '等待中...');
        updateStageProgress(i, 0);
    }
}

// 显示结果区域
function showResult() {
    resultSection.style.display = 'block';
    
    // 从processResults获取实际数据
    const stage1Results = processResults.stage1 || {};
    const stage2Results = processResults.stage2 || {};
    const stage3Results = processResults.stage3 || {};
    
    // 更新统计数据
    const totalFiles = stage1Results.downloaded_files || 0;
    const apiFiles = stage2Results.valid_files || 0;
    const docFiles = totalFiles - apiFiles;
    
    document.getElementById('processedFiles').textContent = totalFiles;
    document.getElementById('totalApis').textContent = apiFiles;
    document.getElementById('totalDocs').textContent = docFiles;
    
    // 设置下载链接
    const downloadYamlLink = document.getElementById('downloadYamlLink');
    const downloadZipLink = document.getElementById('downloadZipLink');
    
    downloadYamlLink.href = '/api/download/complete.yaml';
    downloadZipLink.href = '/api/download/docs.zip';
    
    // 添加点击事件处理
    downloadYamlLink.addEventListener('click', handleDownload);
    downloadZipLink.addEventListener('click', handleDownload);
}

// 处理下载点击事件
function handleDownload(event) {
    const link = event.target;
    const originalText = link.textContent;
    
    // 显示下载状态
    link.textContent = '⏳ 准备下载...';
    link.style.pointerEvents = 'none';
    
    // 恢复原始状态
    setTimeout(() => {
        link.textContent = originalText;
        link.style.pointerEvents = 'auto';
    }, 2000);
}

// 显示错误
function showError(message) {
    errorSection.style.display = 'block';
    document.getElementById('errorMessage').textContent = message;
    addLog(`错误: ${message}`, 'error');
}

// 隐藏结果区域
function hideResultSection() {
    resultSection.style.display = 'none';
}

// 隐藏错误区域
function hideErrorSection() {
    errorSection.style.display = 'none';
}

// 更新按钮状态
function updateButtonState(processing) {
    const btnText = startBtn.querySelector('.btn-text');
    const btnLoading = startBtn.querySelector('.btn-loading');
    
    if (processing) {
        btnText.style.display = 'none';
        btnLoading.style.display = 'inline-flex';
        startBtn.disabled = true;
    } else {
        btnText.style.display = 'inline';
        btnLoading.style.display = 'none';
        startBtn.disabled = false;
    }
}

// 重置并重试
function resetAndRetry() {
    hideErrorSection();
    hideResultSection();
    progressSection.style.display = 'none';
    isProcessing = false;
    currentStage = 0;
    updateButtonState(false);
}

// 验证URL格式
function isValidUrl(string) {
    try {
        new URL(string);
        return true;
    } catch (_) {
        return false;
    }
}

// 处理网络错误
function handleNetworkError(error) {
    if (error.name === 'TypeError' && error.message.includes('fetch')) {
        return '无法连接到服务器，请检查网络连接或服务器状态';
    }
    return error.message || '网络请求失败';
}

// 全局错误处理
window.addEventListener('error', function(event) {
    console.error('全局错误:', event.error);
    if (isProcessing) {
        showError('处理过程中发生意外错误，请重试');
        isProcessing = false;
        updateButtonState(false);
    }
});

// 处理未捕获的Promise错误
window.addEventListener('unhandledrejection', function(event) {
    console.error('未处理的Promise错误:', event.reason);
    if (isProcessing) {
        showError(handleNetworkError(event.reason));
        isProcessing = false;
        updateButtonState(false);
    }
});