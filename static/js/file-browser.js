/**
 * 文件浏览器功能
 * 用于浏览和管理workspace目录中的文件
 */

// 当前路径
let currentPath = '';
// 当前选中的文件
let selectedFile = null;

// 全局变量
let lastFileList = null;
let refreshInterval = null;

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    loadWorkspaceFiles();
    // 设置定时刷新（每5秒）
    refreshInterval = setInterval(checkForFileChanges, 5000);
});

/**
 * 加载workspace目录下的文件列表
 * @param {string} path - 要加载的路径，默认为根目录
 */
async function loadWorkspaceFiles(path = '') {
    try {
        // 更新当前路径
        currentPath = path;
        
        // 更新路径显示
        const pathDisplay = document.getElementById('currentPath');
        pathDisplay.textContent = path ? `Workspace/${path}` : 'Workspace';
        
        // 获取文件列表
        const response = await fetch(`/api/workspace?path=${encodeURIComponent(path)}`);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const files = await response.json();
        lastFileList = files;
        displayFiles(files);
        
        // 如果有文件，自动预览第一个文件
        if (files.length > 0) {
            previewFile(files[0].path);
        }
    } catch (error) {
        console.error('Error loading files:', error);
        const fileList = document.getElementById('fileList');
        fileList.innerHTML = `<div class="file-item error-entry">
            <div class="file-item-name">加载文件失败: ${error.message}</div>
        </div>`;
    }
}

/**
 * 显示文件列表
 * @param {Array} files - 文件列表数据
 */
function displayFiles(files) {
    const fileList = document.getElementById('fileList');
    fileList.innerHTML = '';
    
    // 如果不在根目录，添加返回上级目录选项
    if (currentPath) {
        const parentPath = getParentPath(currentPath);
        const backItem = document.createElement('div');
        backItem.className = 'file-item';
        backItem.innerHTML = `
            <div class="file-item-icon">⬆️</div>
            <div class="file-item-name">返回上级目录</div>
        `;
        backItem.addEventListener('click', () => loadWorkspaceFiles(parentPath));
        fileList.appendChild(backItem);
    }
    
    // 如果没有文件，显示空目录提示
    if (files.length === 0) {
        const emptyItem = document.createElement('div');
        emptyItem.className = 'file-item';
        emptyItem.innerHTML = `
            <div class="file-item-name">空目录</div>
        `;
        fileList.appendChild(emptyItem);
        return;
    }
    
    // 显示文件和目录
    files.forEach(file => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        
        // 格式化文件大小
        const sizeStr = file.size ? formatFileSize(file.size) : '';
        
        // 格式化修改时间
        const dateStr = file.last_modified ? formatDate(new Date(file.last_modified)) : '';
        
        // 根据文件类型设置图标和点击事件
        const isDirectory = file.type === 'directory';
        const icon = isDirectory ? '📁' : getFileIcon(file.name);
        
        fileItem.innerHTML = `
            <div class="file-item-icon ${isDirectory ? 'folder-icon' : 'file-icon'}">${icon}</div>
            <div class="file-item-name">${file.name}</div>
            <div class="file-item-meta">${sizeStr} ${dateStr}</div>
        `;
        
        // 添加点击事件
        if (isDirectory) {
            fileItem.addEventListener('click', () => loadWorkspaceFiles(file.path));
        } else {
            // 文件点击事件，预览文件
            fileItem.addEventListener('click', () => {
                previewFile(file.path);
                
                // 标记选中状态
                if (selectedFile) {
                    selectedFile.classList.remove('selected');
                }
                fileItem.classList.add('selected');
                selectedFile = fileItem;
            });
        }
        
        fileList.appendChild(fileItem);
    });
}

/**
 * 预览文件内容
 * @param {string} filePath - 文件路径
 */
async function previewFile(filePath) {
    try {
        // 使用 /api/file-content 端点获取文件内容
        const response = await fetch(`/api/file-content?path=${encodeURIComponent(filePath)}`);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const content = await response.text();
        
        // 更新预览区域
        document.getElementById('previewFileName').textContent = filePath;
        document.getElementById('previewContent').textContent = content;
    } catch (error) {
        console.error('预览文件失败:', error);
        document.getElementById('previewFileName').textContent = filePath;
        document.getElementById('previewContent').textContent = `加载文件内容失败: ${error.message}`;
    }
}

/**
 * 转义HTML特殊字符
 * @param {string} html - 需要转义的HTML字符串
 * @returns {string} 转义后的字符串
 */
function escapeHtml(html) {
    const div = document.createElement('div');
    div.textContent = html;
    return div.innerHTML;
}

/**
 * 获取上级目录路径
 * @param {string} path - 当前路径
 * @returns {string} 上级目录路径
 */
function getParentPath(path) {
    const parts = path.split('/');
    parts.pop();
    return parts.join('/');
}

/**
 * 根据文件名获取文件图标
 * @param {string} filename - 文件名
 * @returns {string} 文件图标
 */
function getFileIcon(filename) {
    const extension = filename.split('.').pop().toLowerCase();
    
    const iconMap = {
        'txt': '📄',
        'md': '📝',
        'json': '📋',
        'js': '📜',
        'py': '🐍',
        'html': '🌐',
        'css': '🎨',
        'jpg': '🖼️',
        'jpeg': '🖼️',
        'png': '🖼️',
        'gif': '🖼️',
        'pdf': '📑',
        'zip': '🗜️',
        'rar': '🗜️',
        'tar': '🗜️',
        'gz': '🗜️',
        'mp3': '🎵',
        'mp4': '🎬',
        'avi': '🎬',
        'mov': '🎬',
        'exe': '⚙️',
        'sh': '⚙️',
        'bat': '⚙️',
        'dll': '⚙️',
        'so': '⚙️',
        'xml': '📋',
        'csv': '📊',
        'xls': '📊',
        'xlsx': '📊',
        'doc': '📄',
        'docx': '📄',
        'ppt': '📊',
        'pptx': '📊'
    };
    
    return iconMap[extension] || '📄';
}

/**
 * 格式化文件大小
 * @param {number} bytes - 文件大小（字节）
 * @returns {string} 格式化后的文件大小
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    
    return (bytes / Math.pow(1024, i)).toFixed(2) + ' ' + units[i];
}

/**
 * 格式化日期
 * @param {Date} date - 日期对象
 * @returns {string} 格式化后的日期字符串
 */
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    
    return `${year}-${month}-${day} ${hours}:${minutes}`;
}

// 检查文件变化
async function checkForFileChanges() {
    try {
        const response = await fetch('/api/workspace');
        const files = await response.json();
        
        // 检查文件列表是否发生变化
        if (JSON.stringify(files) !== JSON.stringify(lastFileList)) {
            lastFileList = files;
            displayFiles(files);
            
            // 如果有文件且没有文件被选中，自动预览第一个文件
            if (files.length > 0 && document.getElementById('previewFileName').textContent === '未选择文件') {
                previewFile(files[0].path);
            }
        }
    } catch (error) {
        console.error('检查文件更新失败:', error);
    }
}

// 更新文件列表
function updateFileList(files) {
    const fileList = document.getElementById('fileList');
    fileList.innerHTML = '';
    
    files.forEach(file => {
        const fileItem = document.createElement('div');
        fileItem.className = 'file-item';
        fileItem.onclick = () => previewFile(file.path);
        
        const icon = document.createElement('span');
        icon.className = 'file-item-icon';
        icon.textContent = file.type === 'directory' ? '📁' : '📄';
        
        const name = document.createElement('span');
        name.className = 'file-item-name';
        name.textContent = file.name;
        
        const meta = document.createElement('span');
        meta.className = 'file-item-meta';
        meta.textContent = `${file.size} ${file.modified}`;
        
        fileItem.appendChild(icon);
        fileItem.appendChild(name);
        fileItem.appendChild(meta);
        fileList.appendChild(fileItem);
    });
} 