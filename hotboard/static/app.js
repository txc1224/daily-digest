// 自动刷新间隔（毫秒）
const REFRESH_INTERVAL = 5 * 60 * 1000;
const filterState = {
    group: 'all',
    status: 'all',
    query: '',
    sort: 'risk',
};

function setToggleExpanded(button, expanded, expandedLabel, collapsedLabel) {
    if (!button) return;
    button.setAttribute('aria-expanded', expanded ? 'true' : 'false');
    button.textContent = expanded ? expandedLabel : collapsedLabel;
}

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
        const [boardsRes, statusRes] = await Promise.all([
            fetch('/api/boards'),
            fetch('/api/status'),
        ]);
        if (!boardsRes.ok || !statusRes.ok) return;
        const boards = await boardsRes.json();
        const statusPayload = await statusRes.json();

        // 更新各卡片内容
        for (const [platform, board] of Object.entries(boards)) {
            const card = document.querySelector(`[data-platform="${platform}"]`);
            if (!card) continue;
            const platformStatus = statusPayload.platforms?.[platform];

            // 更新时间
            const meta = card.querySelector('.card-meta');
            if (meta && board.updated_at) {
                const time = board.updated_at.substring(11, 19);
                meta.textContent = '更新于 ' + time;
            }

            const statusPill = card.querySelector('.status-pill');
            if (statusPill && platformStatus) {
                statusPill.className = 'status-pill';
                if (platformStatus.consecutive_failures > 0) {
                    statusPill.classList.add('status-failing');
                    statusPill.textContent = '异常';
                } else if ((platformStatus.cache_age_seconds ?? 0) > 600) {
                    statusPill.classList.add('status-stale');
                    statusPill.textContent = '过期';
                } else {
                    statusPill.classList.add('status-healthy');
                    statusPill.textContent = '正常';
                }
            }

            const toolbar = card.querySelector('.card-toolbar');
            if (toolbar && platformStatus) {
                const pills = [
                    `<span class="toolbar-pill">${board.items?.length || 0} 条</span>`,
                ];
                if (platformStatus.last_duration_ms != null) {
                    pills.push(`<span class="toolbar-pill">${platformStatus.last_duration_ms}ms</span>`);
                }
                if (platformStatus.cache_age_seconds != null) {
                    pills.push(`<span class="toolbar-pill">缓存 ${platformStatus.cache_age_seconds}s</span>`);
                }
                toolbar.innerHTML = pills.join('');
            }

            const alertBox = card.querySelector('.card-alert');
            if (platformStatus?.last_error) {
                if (alertBox) {
                    alertBox.textContent = platformStatus.last_error;
                } else {
                    const el = document.createElement('div');
                    el.className = 'card-alert';
                    el.textContent = platformStatus.last_error;
                    card.appendChild(el);
                }
            } else if (alertBox) {
                alertBox.remove();
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

        renderHealth(statusPayload.health);
        applyFilters();
        updateTime();
    } catch (e) {
        console.error('Auto refresh failed:', e);
    }
}

function renderHealth(health) {
    if (!health) return;

    const healthyCount = document.getElementById('healthy-count');
    const failingCount = document.getElementById('failing-count');
    const staleCount = document.getElementById('stale-count');
    if (healthyCount) healthyCount.textContent = `${health.healthy_count}/${health.enabled_count}`;
    if (failingCount) failingCount.textContent = String(health.failing_count);
    if (staleCount) staleCount.textContent = String(health.stale_count);

    const failingList = document.getElementById('failing-platforms');
    if (failingList) {
        const items = health.failing_platforms || [];
        failingList.innerHTML = items.length
            ? items.map(item => `<li><strong>${escapeHtml(item.name)}</strong><span>失败 ${item.consecutive_failures} 次</span>${item.last_error ? `<em>${escapeHtml(item.last_error)}</em>` : ''}</li>`).join('')
            : '<li class="health-empty">暂无异常平台</li>';
    }

    const slowList = document.getElementById('slow-platforms');
    if (slowList) {
        const items = health.slow_platforms || [];
        slowList.innerHTML = items.length
            ? items.map(item => `<li><strong>${escapeHtml(item.name)}</strong><span>${item.last_duration_ms}ms</span><em>${item.last_item_count} 条</em></li>`).join('')
            : '<li class="health-empty">暂无抓取记录</li>';
    }
}

function getCardStatus(card) {
    const pill = card.querySelector('.status-pill');
    if (!pill) return 'healthy';
    if (pill.classList.contains('status-failing')) return 'failing';
    if (pill.classList.contains('status-stale')) return 'stale';
    return 'healthy';
}

function getCardSearchText(card) {
    const title = card.querySelector('.card-title')?.textContent || '';
    const items = Array.from(card.querySelectorAll('.item-title')).slice(0, 8).map(node => node.textContent || '');
    return `${title} ${items.join(' ')}`.toLowerCase();
}

function getCardRiskScore(card) {
    const status = getCardStatus(card);
    if (status === 'failing') return 2;
    if (status === 'stale') return 1;
    return 0;
}

function getCardUpdatedTime(card) {
    const text = card.querySelector('.card-meta')?.textContent || '';
    const match = text.match(/(\d{2}):(\d{2}):(\d{2})/);
    if (!match) return -1;
    return Number(match[1]) * 3600 + Number(match[2]) * 60 + Number(match[3]);
}

function sortCardsWithinSections() {
    const sections = Array.from(document.querySelectorAll('.group-section'));
    sections.forEach((section) => {
        const grid = section.querySelector('.boards-grid');
        if (!grid) return;
        const cards = Array.from(grid.querySelectorAll('.board-card'));

        cards.sort((a, b) => {
            if (filterState.sort === 'updated') {
                return getCardUpdatedTime(b) - getCardUpdatedTime(a);
            }

            if (filterState.sort === 'risk') {
                const riskDiff = getCardRiskScore(b) - getCardRiskScore(a);
                if (riskDiff !== 0) return riskDiff;
            }

            const aTitle = a.querySelector('.card-title')?.textContent || '';
            const bTitle = b.querySelector('.card-title')?.textContent || '';
            return aTitle.localeCompare(bTitle, 'zh-CN');
        });

        cards.forEach((card) => grid.appendChild(card));
    });
}

function applyFilters() {
    const cards = Array.from(document.querySelectorAll('.board-card'));
    const sections = Array.from(document.querySelectorAll('.group-section'));
    let visibleCount = 0;

    sortCardsWithinSections();

    cards.forEach((card) => {
        const group = card.dataset.group || 'all';
        const status = getCardStatus(card);
        const searchText = getCardSearchText(card);
        const matchesGroup = filterState.group === 'all' || filterState.group === group;
        const matchesStatus = filterState.status === 'all' || filterState.status === status;
        const matchesQuery = !filterState.query || searchText.includes(filterState.query);
        const visible = matchesGroup && matchesStatus && matchesQuery;
        card.style.display = visible ? '' : 'none';
        if (visible) visibleCount += 1;
    });

    sections.forEach((section) => {
        const visibleCards = section.querySelectorAll('.board-card:not([style*="display: none"])');
        section.style.display = visibleCards.length ? '' : 'none';
    });

    const summary = document.getElementById('filter-summary');
    const mobileCount = document.getElementById('filter-mobile-count');
    if (summary) {
        const parts = [];
        if (filterState.group !== 'all') parts.push(`分组: ${filterState.group}`);
        if (filterState.status !== 'all') parts.push(`状态: ${filterState.status}`);
        if (filterState.query) parts.push(`搜索: ${filterState.query}`);
        if (filterState.sort !== 'risk') parts.push(`排序: ${filterState.sort}`);
        if (filterState.sort === 'risk' && parts.length) parts.push('排序: 异常优先');
        summary.textContent = parts.length
            ? `已筛选 ${visibleCount} 个平台 · ${parts.join(' · ')}`
            : `显示全部平台 · 共 ${visibleCount} 个`;
        if (mobileCount) {
            mobileCount.textContent = parts.length
                ? `${visibleCount} 个结果`
                : `全部平台 · ${visibleCount} 个`;
        }
    } else if (mobileCount) {
        mobileCount.textContent = `全部平台 · ${visibleCount} 个`;
    }
}

function bindFilterButtons(containerId, key, attr) {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.addEventListener('click', (event) => {
        const button = event.target.closest('.filter-chip');
        if (!button) return;
        container.querySelectorAll('.filter-chip').forEach((chip) => chip.classList.remove('active'));
        button.classList.add('active');
        filterState[key] = button.dataset[attr] || 'all';
        applyFilters();
    });
}

function initFilters() {
    bindFilterButtons('group-filters', 'group', 'filterGroup');
    bindFilterButtons('status-filters', 'status', 'filterStatus');
    bindFilterButtons('sort-filters', 'sort', 'filterSort');

    const search = document.getElementById('board-search');
    if (search) {
        search.addEventListener('input', (event) => {
            filterState.query = (event.target.value || '').trim().toLowerCase();
            applyFilters();
        });
    }

    applyFilters();
}

function initResponsivePanels() {
    const filterSection = document.getElementById('filter-section');
    const filterToggle = document.getElementById('filter-toggle');
    const healthDetailGrid = document.getElementById('health-detail-grid');
    const healthToggle = document.getElementById('health-toggle');

    if (filterSection && filterToggle) {
        filterToggle.addEventListener('click', () => {
            const expanded = filterSection.classList.toggle('is-open');
            setToggleExpanded(filterToggle, expanded, '收起筛选', '展开筛选');
        });
        setToggleExpanded(filterToggle, false, '收起筛选', '展开筛选');
    }

    if (healthDetailGrid && healthToggle) {
        healthToggle.addEventListener('click', () => {
            const expanded = healthDetailGrid.classList.toggle('is-open');
            setToggleExpanded(healthToggle, expanded, '收起详情', '展开详情');
        });
        setToggleExpanded(healthToggle, false, '收起详情', '展开详情');
    } else if (healthToggle) {
        healthToggle.style.display = 'none';
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text || '';
    return div.innerHTML;
}

// 初始化
updateTime();
initResponsivePanels();
initFilters();
setInterval(autoRefresh, REFRESH_INTERVAL);
