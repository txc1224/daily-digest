// 自动刷新间隔（毫秒）
const REFRESH_INTERVAL = 5 * 60 * 1000;

function updateTime() {
    const el = document.getElementById('update-time');
    if (el) {
        const now = new Date();
        el.textContent = '最后刷新: ' + now.toLocaleTimeString('zh-CN', { hour12: false });
    }
}

async function manualRefresh() {
    const btn = document.getElementById('refresh-btn');
    btn.disabled = true;
    btn.textContent = '⏳ 刷新中...';

    try {
        const res = await fetch('/api/refresh', { method: 'POST' });
        if (res.ok) {
            // 刷新页面以获取最新数据
            window.location.reload();
        } else {
            alert('刷新失败，请重试');
        }
    } catch (e) {
        alert('网络错误: ' + e.message);
    } finally {
        btn.disabled = false;
        btn.textContent = '🔄 刷新';
    }
}

async function autoRefresh() {
    try {
        const res = await fetch('/api/boards');
        if (!res.ok) return;
        const boards = await res.json();

        // 更新各卡片内容
        for (const [platform, board] of Object.entries(boards)) {
            const card = document.querySelector(`[data-platform="${platform}"]`);
            if (!card) continue;

            // 更新时间
            const meta = card.querySelector('.card-meta');
            if (meta && board.updated_at) {
                const time = board.updated_at.substring(11, 19);
                meta.textContent = '更新于 ' + time;
            }

            // 更新列表
            const list = card.querySelector('.hot-list');
            if (!list || !board.items) continue;

            list.innerHTML = board.items.slice(0, 20).map(item => {
                const topClass = item.rank <= 3 ? ` top-${item.rank}` : '';
                const hotHtml = item.hot_value ? `<span class="item-hot">${escapeHtml(item.hot_value)}</span>` : '';
                return `<li class="hot-item${topClass}">
                    <span class="item-rank">${item.rank}</span>
                    <a href="${escapeHtml(item.url)}" target="_blank" class="item-title" title="${escapeHtml(item.title)}">${escapeHtml(item.title)}</a>
                    ${hotHtml}
                </li>`;
            }).join('');
        }

        updateTime();
    } catch (e) {
        console.error('Auto refresh failed:', e);
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
}

// 初始化
updateTime();
setInterval(autoRefresh, REFRESH_INTERVAL);
