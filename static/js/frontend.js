let eventSource = null;
let cur_task_id = null;

async function executePrompt() {
    // 获取用户输入
    const userPrompt = document.getElementById('input').value;
    
    if (!userPrompt.trim()) {
        appendToOutput("请输入需求内容后再执行任务", "error");
        return;
    }
    
    // 显示用户输入的消息
    appendToOutput(userPrompt, "user");
    
    // 清空输入框
    document.getElementById('input').value = '';
    
    // 显示正在处理的消息
    appendToOutput("正在处理您的请求...", "info");
    
    // 使用默认配置执行任务
    const config = {
        deploy_type: "local",
        model_name: "default",
        api_key: "",
        prompt: userPrompt
    };

    try {
        // 启动任务
        const response = await fetch('/execute', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(config)
        });
        
        if (!response.ok) {
            throw new Error(`服务器响应错误: ${response.status}`);
        }
        
        const { task_id } = await response.json();
        cur_task_id = task_id;
        
        // 连接流式端点
        connectToEventStream(task_id);
    } catch (error) {
        appendToOutput(`执行任务失败: ${error.message}`, "error");
    }
}

function connectToEventStream(task_id) {
    // 关闭之前的连接
    if (eventSource) {
        eventSource.close();
    }
    
    // 连接流式端点
    eventSource = new EventSource(`/stream/${task_id}`);

    eventSource.onmessage = (e) => {
        const jsonStr = e.data.replace(/^data:/, '');
        const data = JSON.parse(jsonStr);
        appendToOutput(data.content, data.type || "system");
    };

    eventSource.onerror = () => {
        eventSource.close();
        eventSource = null;
        appendToOutput("连接中断", "error");
    };
}

function stopExecution() {
    if (eventSource) {
        eventSource.close();
        fetch(`/stop/${cur_task_id}`, { method: 'POST' });
        appendToOutput("任务已停止", "info");
        eventSource = null;
    } else {
        appendToOutput("没有正在执行的任务", "info");
    }
}

function appendToOutput(message, type = "log") {
    const outputDiv = document.getElementById('output');
    
    // 创建新的消息元素
    const messageElement = document.createElement('div');
    messageElement.className = `message ${type}-message`;
    
    // 设置消息内容
    if (typeof message === 'object') {
        messageElement.textContent = JSON.stringify(message);
    } else {
        messageElement.textContent = message;
    }
    
    // 根据消息类型设置样式
    switch (type) {
        case "error":
            messageElement.style.color = "#ff4444";
            messageElement.style.backgroundColor = "#ffebee";
            messageElement.style.alignSelf = "flex-start";
            messageElement.style.borderRadius = "12px 12px 12px 0";
            messageElement.style.padding = "8px 12px";
            messageElement.style.margin = "4px 0";
            messageElement.style.maxWidth = "80%";
            break;
        case "info":
            messageElement.style.color = "#4444ff";
            messageElement.style.backgroundColor = "#e3f2fd";
            messageElement.style.alignSelf = "flex-start";
            messageElement.style.borderRadius = "12px 12px 12px 0";
            messageElement.style.padding = "8px 12px";
            messageElement.style.margin = "4px 0";
            messageElement.style.maxWidth = "80%";
            break;
        case "user":
            messageElement.style.color = "#ffffff";
            messageElement.style.backgroundColor = "#007bff";
            messageElement.style.alignSelf = "flex-end";
            messageElement.style.borderRadius = "12px 12px 0 12px";
            messageElement.style.padding = "8px 12px";
            messageElement.style.margin = "4px 0";
            messageElement.style.maxWidth = "80%";
            break;
        case "system":
            messageElement.style.color = "#333333";
            messageElement.style.backgroundColor = "#f1f0f0";
            messageElement.style.alignSelf = "flex-start";
            messageElement.style.borderRadius = "12px 12px 12px 0";
            messageElement.style.padding = "8px 12px";
            messageElement.style.margin = "4px 0";
            messageElement.style.maxWidth = "80%";
            break;
        default:
            messageElement.style.color = "#333333";
            messageElement.style.backgroundColor = "#f1f0f0";
            messageElement.style.alignSelf = "flex-start";
            messageElement.style.borderRadius = "12px 12px 12px 0";
            messageElement.style.padding = "8px 12px";
            messageElement.style.margin = "4px 0";
            messageElement.style.maxWidth = "80%";
    }
    
    // 添加到输出区域
    outputDiv.appendChild(messageElement);
    
    // 滚动到底部
    outputDiv.scrollTop = outputDiv.scrollHeight;
}