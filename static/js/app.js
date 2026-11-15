/* 云通讯录前端逻辑：渲染联系人、收藏、搜索、多联系方式编辑、导入导出 */
(() => {
    "use strict";

    const TYPE_LABEL = { phone: "电话", email: "邮箱", social: "社交", address: "地址" };
    const TYPE_ORDER = ["phone", "email", "social", "address"];
    const AVATAR_COLORS = ["#4f6df5", "#10b981", "#f59e0b", "#8b5cf6", "#ef4444", "#0ea5e9", "#d946ef", "#14b8a6"];

    const $ = (sel) => document.querySelector(sel);

    const state = { contacts: [], keyword: "" };

    // ---------------------------------------------------------- utilities
    function toast(msg, type = "ok") {
        const el = document.createElement("div");
        el.className = `toast ${type}`;
        el.textContent = msg;
        $("#toastBox").appendChild(el);
        setTimeout(() => el.remove(), 2600);
    }

    function colorOf(name) {
        let h = 0;
        for (const ch of name) h = (h * 31 + ch.codePointAt(0)) >>> 0;
        return AVATAR_COLORS[h % AVATAR_COLORS.length];
    }

    function detailOf(contact, type) {
        const d = contact.details.find((x) => x.type === type);
        return d ? d.value : "";
    }

    async function api(url, options = {}) {
        const res = await fetch(url, options);
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(data.error || `请求失败(${res.status})`);
        return data;
    }

    // ------------------------------------------------------------- render
    function render() {
        const list = state.contacts;
        const favs = list.filter((c) => c.favorite);

        $("#favSection").hidden = favs.length === 0;
        $("#favGrid").innerHTML = favs.map((c) => `
            <div class="fav-card" data-id="${c.id}" title="点击编辑 ${c.name}">
                <div class="avatar" style="background:${colorOf(c.name)}">${c.name.slice(0, 1).toUpperCase()}</div>
                <div class="fav-name">${escapeHtml(c.name)}</div>
                <div class="fav-sub">${escapeHtml(detailOf(c, "phone") || detailOf(c, "email") || "无联系方式")}</div>
            </div>`).join("");

        $("#contactCount").textContent = list.length;
        $("#contactGrid").innerHTML = list.map(cardHtml).join("");
        $("#emptyState").hidden = list.length !== 0;
    }

    function cardHtml(c) {
        const details = TYPE_ORDER.flatMap((t) =>
            c.details.filter((d) => d.type === t).map((d) => ({ type: t, value: d.value }))
        );
        return `
        <div class="contact-card" data-id="${c.id}">
            <div class="card-head">
                <div class="avatar" style="background:${colorOf(c.name)}">${c.name.slice(0, 1).toUpperCase()}</div>
                <div>
                    <div class="card-name">${escapeHtml(c.name)}</div>
                    <div class="card-notes" title="${escapeHtml(c.notes)}">${escapeHtml(c.notes || "")}</div>
                </div>
                <div class="card-actions">
                    <button class="icon-btn star-btn ${c.favorite ? "active" : ""}" data-act="fav"
                            title="${c.favorite ? "取消收藏" : "设为常用联系人"}">${c.favorite ? "★" : "☆"}</button>
                    <button class="icon-btn" data-act="edit" title="编辑">✏️</button>
                    <button class="icon-btn del" data-act="del" title="删除">🗑️</button>
                </div>
            </div>
            <div class="detail-list">
                ${details.map((d) => `
                    <div class="detail-item">
                        <span class="detail-tag tag-${d.type}">${TYPE_LABEL[d.type]}</span>
                        <span class="detail-value">${escapeHtml(d.value)}</span>
                    </div>`).join("")}
                ${details.length === 0 ? '<div class="detail-item"><span class="detail-value" style="color:#9aa3b2">暂无联系方式</span></div>' : ""}
            </div>
        </div>`;
    }

    function escapeHtml(s) {
        return String(s ?? "").replace(/[&<>"']/g, (ch) => ({
            "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
        }[ch]));
    }

    async function reload() {
        const url = state.keyword ? `/api/contacts?q=${encodeURIComponent(state.keyword)}` : "/api/contacts";
        state.contacts = await api(url);
        render();
    }

    // -------------------------------------------------------- modal logic
    let editingId = null;

    function openModal(contact = null) {
        editingId = contact ? contact.id : null;
        $("#modalTitle").textContent = contact ? "编辑联系人" : "新建联系人";
        $("#fName").value = contact ? contact.name : "";
        $("#fNotes").value = contact ? contact.notes : "";
        $("#detailRows").innerHTML = "";
        const details = contact ? contact.details : [];
        if (details.length === 0) addDetailRow("phone", "");
        details.forEach((d) => addDetailRow(d.type, d.value));
        $("#modalMask").hidden = false;
        $("#fName").focus();
    }

    function closeModal() {
        $("#modalMask").hidden = true;
        editingId = null;
    }

    function addDetailRow(type = "phone", value = "") {
        const row = document.createElement("div");
        row.className = "detail-row";
        const options = TYPE_ORDER.map((t) =>
            `<option value="${t}" ${t === type ? "selected" : ""}>${TYPE_LABEL[t]}</option>`).join("");
        row.innerHTML = `
            <select>${options}</select>
            <input type="text" placeholder="请输入内容（留空将被忽略）" value="${escapeHtml(value)}">
            <button type="button" class="del-detail" title="删除此条">✕</button>`;
        row.querySelector(".del-detail").addEventListener("click", () => row.remove());
        $("#detailRows").appendChild(row);
        row.querySelector("input").focus();
    }

    async function saveContact(e) {
        e.preventDefault();
        const name = $("#fName").value.trim();
        if (!name) { toast("姓名不能为空", "err"); return; }
        const details = [...document.querySelectorAll("#detailRows .detail-row")]
            .map((row) => ({
                type: row.querySelector("select").value,
                value: row.querySelector("input").value.trim(),
            }))
            .filter((d) => d.value);
        const payload = { name, notes: $("#fNotes").value.trim(), details };
        try {
            if (editingId) {
                await api(`/api/contacts/${editingId}`, {
                    method: "PUT",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload),
                });
                toast("已保存修改");
            } else {
                await api("/api/contacts", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify(payload),
                });
                toast("新建联系人成功");
            }
            closeModal();
            await reload();
        } catch (err) {
            toast(err.message, "err");
        }
    }

    // -------------------------------------------------------- list events
    document.addEventListener("click", async (e) => {
        const favCard = e.target.closest(".fav-card");
        if (favCard) {
            const contact = state.contacts.find((c) => c.id === Number(favCard.dataset.id));
            if (contact) openModal(contact);
            return;
        }

        const btn = e.target.closest("[data-act]");
        if (!btn) return;
        const card = btn.closest(".contact-card, .fav-card");
        const id = Number(card.dataset.id);
        const act = btn.dataset.act;

        if (act === "fav") {
            try {
                const r = await api(`/api/contacts/${id}/favorite`, { method: "PATCH" });
                toast(r.favorite ? `已收藏「${state.contacts.find((c) => c.id === id)?.name ?? ""}」为常用联系人` : "已取消收藏");
                await reload();
            } catch (err) { toast(err.message, "err"); }
        } else if (act === "edit") {
            const contact = state.contacts.find((c) => c.id === id);
            if (contact) openModal(contact);
        } else if (act === "del") {
            const name = state.contacts.find((c) => c.id === id)?.name ?? "该联系人";
            if (!confirm(`确定删除「${name}」吗？删除后无法恢复。`)) return;
            try {
                await api(`/api/contacts/${id}`, { method: "DELETE" });
                toast("已删除");
                await reload();
            } catch (err) { toast(err.message, "err"); }
        }
    });

    // ------------------------------------------------------ toolbar events
    let searchTimer = null;
    $("#searchInput").addEventListener("input", (e) => {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(async () => {
            state.keyword = e.target.value.trim();
            await reload();
        }, 200);
    });

    $("#btnAdd").addEventListener("click", () => openModal());
    $("#btnCloseModal").addEventListener("click", closeModal);
    $("#btnCancel").addEventListener("click", closeModal);
    $("#modalMask").addEventListener("click", (e) => {
        if (e.target === $("#modalMask")) closeModal();
    });
    $("#contactForm").addEventListener("submit", saveContact);
    document.querySelectorAll(".chip[data-add-type]").forEach((chip) =>
        chip.addEventListener("click", () => addDetailRow(chip.dataset.addType)));

    $("#btnExport").addEventListener("click", () => {
        window.location.href = "/api/export";
        toast("正在导出 Excel…");
    });

    $("#btnImport").addEventListener("click", () => $("#importFile").click());
    $("#importFile").addEventListener("change", async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const fd = new FormData();
        fd.append("file", file);
        try {
            const r = await api("/api/import", { method: "POST", body: fd });
            toast(`导入成功：新增 ${r.imported} 人${r.skipped ? `，跳过 ${r.skipped} 行` : ""}`);
            await reload();
        } catch (err) {
            toast(err.message, "err");
        } finally {
            e.target.value = "";
        }
    });

    reload();
})();
