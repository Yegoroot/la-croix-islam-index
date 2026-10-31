#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, re, html, os, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(HERE, "lacroix_idx.json"), encoding="utf-8"))
ann_path = os.path.join(HERE, "annotations.json")
ANN = json.load(open(ann_path, encoding="utf-8")) if os.path.exists(ann_path) else {}

FR_MONTHS = {"janv":"01","févr":"02","fevr":"02","mars":"03","avr":"04","mai":"05",
    "juin":"06","juil":"07","août":"08","aout":"08","sept":"09","oct":"10",
    "nov":"11","déc":"12","dec":"12"}

def date_from_url(u):
    m = re.search(r'-(20\d{2})(\d{2})(\d{2})(?:\D|$)', u)
    if m and 1<=int(m.group(2))<=12 and 1<=int(m.group(3))<=31:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    m = re.search(r'-(\d{4})-(\d{2})-(\d{2})-', u)
    if m and 1<=int(m.group(2))<=12 and 1<=int(m.group(3))<=31:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    return ""

def date_from_fr(s):
    if not s: return ""
    if re.match(r'^\d{4}-\d{2}-\d{2}$', s): return s
    m = re.match(r'^(\d{1,2})\s+([^\s.]+)\.?\s+(\d{4})$', s.strip())
    if m:
        day, mon, year = m.groups(); mon = mon.lower()
        for k,v in FR_MONTHS.items():
            if mon.startswith(k): return f"{year}-{v}-{int(day):02d}"
    return ""

def norm_date(rec): return date_from_url(rec["u"]) or date_from_fr(rec.get("d","")) or ""

RUBR = {"religion":"Religion","Religion":"Religion","Monde":"Monde","international":"International",
    "Debats":"Débats","France":"France","a-vif":"À vif","Culture":"Culture","culture":"Culture",
    "societe":"Société","Economie":"Économie","Definitions":"Définitions","Abonnes":"Abonnés",
    "Actualite":"Actualité","Urbi-et-Orbi":"Urbi & Orbi","Les-formations-Croire.com":"Formations Croire",
    "tag":"Dossier","Articles-du-Forum":"Forum","Theologie":"Théologie"}
def rubrique(rec):
    s = rec.get("s","")
    if s in RUBR: return RUBR[s]
    if re.search(r'\d{4}', s) or len(s) > 30: return "—"
    return s or "—"

def pretty_date(iso):
    if not iso: return "—"
    try:
        y,m,d = iso.split("-"); return f"{d}.{m}.{y}"
    except Exception: return iso

# (code, ru, fr, ar)
STRUCT = [
 ("1","Глава","Chapitre","Статьи о вероубеждении и поклонении","Articles sur la croyance et le culte",
  "المقالات المتعلقة بالعقيدة والعبادات",[
    ("1.1","Исламское единобожие","Le monothéisme islamique (tawhid)","التوحيد الإسلامي"),
    ("1.2","Пророки, посланники и небесные послания","Les prophètes, messagers et révélations","الأنبياء والرسل والرسالات السماوية"),
    ("1.3","Исламские виды поклонения","Les actes de culte en islam","العبادات الإسلامية"),
    ("1.4","Источники исламского шариата","Les sources de la charia","مصادر الشريعة الإسلامية"),
 ]),
 ("2","Глава","Chapitre","Шариатская политика и властные установления","Politique légale et gouvernance",
  "السياسة الشرعية والأحكام السلطانية",[
    ("2.1","Имамат и исламский халифат","L'imamat et le califat","الإمامة والخلافة الإسلامية"),
    ("2.2","Джихад и шариатская политика","Le djihad et la politique légale","الجهاد والسياسة الشرعية"),
    ("2.3","Шариатские наказания (худуд и тазир)","Les peines légales (hudud et ta'zir)","الحدود الشرعية والتعزيرات"),
 ]),
 ("3","Глава","Chapitre","Семья и мусульманка","La famille et la femme musulmane",
  "الأسرة والمرأة المسلمة",[
    ("3.1","Брак и многожёнство","Le mariage et la polygamie","الزواج والتعدد"),
    ("3.2","Хиджаб и свобода мусульманки","Le voile et la liberté de la femme musulmane","الحجاب وحرية المرأة المسلمة"),
    ("3.3","Смешение полов и равенство мужчин и женщин","La mixité et l'égalité hommes-femmes","الاختلاط والمساواة بين الذكور والإناث"),
    ("3.4","Опекун (вали) и махрам мусульманки","Le tuteur (wali) et le mahram","ولي المرأة المسلمة ومحرمها"),
 ]),
 ("4","Глава","Chapitre","Исламские страны и регионы","Pays et régions de l'islam",
  "البلدان والأمصار الإسلامية",[
    ("4.1","Страны арабского Машрика","Les pays du Machrek arabe","دول المشرق العربي"),
    ("4.2","Страны арабского Магриба","Les pays du Maghreb arabe","دول المغرب العربي"),
    ("4.3","Страны Африки и Азии","Les pays d'Afrique et d'Asie","دول أفريقيا وآسيا"),
    ("4.4","Регион Кавказа и Балкан","Le Caucase et les Balkans","منطقة القوقاز والبلقان"),
    ("4.5","Эмигранты, диаспоры и мусульманские меньшинства на Западе","Expatriés et minorités musulmanes en Occident","قضايا المغتربين والجاليات والأقليات المسلمة في الدول الغربية"),
 ]),
 ("5","Глава","Chapitre","Течения, партии, мазхабы и личности","Courants, partis, écoles et figures",
  "الفرق والأحزاب والمذاهب والشخصيات الإسلامية",[
    ("5.1","Ахлю-с-Сунна валь-Джамаа и фикховые школы","Les sunnites et les écoles juridiques","أهل السنة والجماعة والمدارس الفقهية الإسلامية"),
    ("5.2","Исламские секты и течения","Les courants et sectes de l'islam","الفرق الإسلامية"),
    ("5.3","Исламские партии и джамааты","Les partis et groupes islamiques","الأحزاب والجماعات الإسلامية"),
    ("5.4","Сподвижники, праведные предшественники и учёные","Compagnons, pieux prédécesseurs et savants","الصحابة والسلف الصالح والعلماء"),
    ("5.5","Призыв шейха Мухаммада ибн Абдуль-Ваххаба","La prédication de M. ben Abdelwahhab","دعوة الشيخ محمد بن عبد الوهاب"),
 ]),
]

by_code = {}
for r in data:
    by_code.setdefault(r["c"], []).append(r)
for c in by_code:
    for r in by_code[c]:
        r["_iso"] = norm_date(r)
    by_code[c].sort(key=lambda r: r["_iso"] or "0000", reverse=True)

def esc(s): return html.escape(s or "", quote=True)
def clean_title(t):
    t=(t or "").strip(); return re.sub(r'\s*\.\.\.$',' …',t)
def i18n(ru, fr, tag="span", cls=""):
    c = (' class="i18n '+cls+'"') if cls else ' class="i18n"'
    return f'<{tag}{c} data-ru="{esc(ru)}" data-fr="{esc(fr)}">{esc(ru)}</{tag}>'

today = datetime.date.today().strftime("%d.%m.%Y")
total = len(data)
n_ann = sum(1 for r in data if r["u"] in ANN)

body = []
toc = []
for (num, ch_ru_lbl, ch_fr_lbl, ch_ru, ch_fr, ch_ar, subs) in STRUCT:
    ch_id = "ch"+num
    toc.append(f'<li><a href="#{ch_id}"><b>{i18n(ch_ru_lbl, ch_fr_lbl)} {num}.</b> '
               f'{i18n(ch_ru, ch_fr)} <span class="ar">{esc(ch_ar)}</span></a></li>')
    body.append(f'<section class="chap" id="{ch_id}">')
    body.append(f'<h2><span class="chnum">{i18n(ch_ru_lbl, ch_fr_lbl)} {num}</span> '
                f'{i18n(ch_ru, ch_fr)}</h2>'
                f'<div class="ar block chtheme">{esc(ch_ar)}</div>')
    for (code, ru, fr, ar) in subs:
        recs = by_code.get(code, [])
        body.append('<div class="topic">')
        body.append(f'<h3><span class="tnum">{code}</span> {i18n(ru, fr)} '
                    f'<span class="ar">{esc(ar)}</span><span class="cnt">{len(recs)}</span></h3>')
        if not recs:
            body.append(f'<p class="empty">{i18n("— статей по этой теме не найдено —","— aucun article trouvé pour ce thème —")}</p>')
        else:
            body.append('<table><thead><tr>'
                f'<th class="num">№</th>'
                f'<th>{i18n("Статья (ссылка)","Article (lien)")}</th>'
                f'<th class="au">{i18n("Автор","Auteur")}</th>'
                f'<th class="rub">{i18n("Рубрика","Rubrique")}</th>'
                f'<th class="dt">{i18n("Дата","Date")}</th>'
                '</tr></thead><tbody>')
            for i, r in enumerate(recs, 1):
                a = ANN.get(r["u"], {})
                author = a.get("author","") or "—"
                arnote = a.get("ar","")
                btn = (f'<button class="noteBtn" type="button" aria-expanded="false">'
                       f'<span class="i18n" data-ru="ملخص عربي" data-fr="ملخص عربي">ملخص عربي</span> ▾</button>') if arnote else ""
                body.append('<tr class="art">'
                    f'<td class="num">{i}</td>'
                    f'<td class="ttl"><a href="{esc(r["u"])}" target="_blank" rel="noopener">{esc(clean_title(r["t"]))}</a> {btn}</td>'
                    f'<td class="au copyable" title="клик — скопировать / cliquer pour copier">{esc(author)}</td>'
                    f'<td class="rub">{esc(rubrique(r))}</td>'
                    f'<td class="dt copyable" title="клик — скопировать / cliquer pour copier">{pretty_date(r["_iso"])}</td>'
                    '</tr>')
                if arnote:
                    body.append('<tr class="note" style="display:none"><td class="num"></td>'
                        f'<td colspan="4"><div class="ar-note" dir="rtl" lang="ar">{esc(arnote)}</div></td></tr>')
            body.append('</tbody></table>')
        body.append('</div>')
    body.append('</section>')

doc = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Образ ислама в газете La Croix — указатель статей</title>
<style>
  :root{{--bg:#f6f4ef;--card:#fff;--ink:#23201b;--muted:#6b6459;--line:#e4ded3;
         --accent:#9c3b2e;--accent2:#1f5a73;--hover:#faf7f1;}}
  *{{box-sizing:border-box}}
  body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 "Georgia","Times New Roman",serif;}}
  .wrap{{max-width:1000px;margin:0 auto;padding:28px 20px 80px;}}
  header.top{{border-bottom:3px double var(--accent);padding-bottom:16px;margin-bottom:8px;
     display:flex;justify-content:space-between;align-items:flex-start;gap:16px;flex-wrap:wrap;}}
  h1{{font-size:26px;margin:0 0 6px;color:var(--accent);line-height:1.25;}}
  .sub{{color:var(--muted);font-size:15px;}}
  .langsw{{flex:0 0 auto;font-family:sans-serif;font-size:13px;white-space:nowrap;}}
  .langsw button{{border:1px solid var(--line);background:var(--card);color:var(--muted);
     padding:5px 12px;cursor:pointer;font:inherit;}}
  .langsw button:first-of-type{{border-radius:6px 0 0 6px;}} .langsw button:last-of-type{{border-radius:0 6px 6px 0;border-left:none;}}
  .langsw button.on{{background:var(--accent);color:#fff;border-color:var(--accent);}}
  .ar{{font-family:"Geeza Pro","Scheherazade New","Amiri","Times New Roman",serif;
       direction:rtl;unicode-bidi:isolate;color:var(--accent2);font-size:.95em;}}
  .ar.block{{display:block;font-size:16px;margin-top:4px;}}
  .meta{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 18px;
     margin:18px 0 22px;font-size:14px;color:var(--muted);}}
  .meta b{{color:var(--ink);}}
  nav.toc{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 20px;margin-bottom:30px;}}
  nav.toc ul{{margin:6px 0 0;padding-left:20px;}}
  nav.toc a{{color:var(--ink);text-decoration:none;}} nav.toc a:hover{{color:var(--accent);}}
  section.chap{{margin:30px 0;}}
  h2{{font-size:21px;color:var(--ink);border-bottom:2px solid var(--accent);padding-bottom:8px;margin:0 0 4px;}}
  .chnum{{background:var(--accent);color:#fff;font-size:13px;padding:2px 10px;border-radius:20px;margin-right:10px;vertical-align:middle;}}
  .chtheme{{margin:0 0 12px;}}
  .topic{{margin:16px 0 24px;}}
  h3{{font-size:17px;margin:0 0 8px;color:var(--accent2);display:flex;align-items:center;gap:10px;flex-wrap:wrap;}}
  .tnum{{font-family:monospace;background:#eef2f3;color:var(--accent2);padding:1px 8px;border-radius:5px;font-size:14px;}}
  .cnt{{margin-left:auto;background:#eee;color:var(--muted);border-radius:20px;padding:1px 10px;font-size:12px;font-family:sans-serif;}}
  table{{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);border-radius:8px;overflow:hidden;font-size:15px;}}
  thead th{{background:#efe9df;text-align:left;font-size:12px;letter-spacing:.03em;text-transform:uppercase;color:var(--muted);padding:8px 10px;font-weight:bold;}}
  td{{padding:9px 10px;border-top:1px solid var(--line);vertical-align:top;}}
  tr.art:hover td{{background:var(--hover);}}
  td.num{{width:34px;color:var(--muted);text-align:right;font-family:monospace;font-size:13px;}} th.num{{text-align:right;}}
  td.ttl a{{color:var(--accent);text-decoration:none;}} td.ttl a:hover{{text-decoration:underline;}}
  td.au,th.au{{width:140px;font-size:13px;color:var(--ink);}}
  td.rub,th.rub{{width:110px;color:var(--accent2);font-size:13px;white-space:nowrap;}}
  td.dt,th.dt{{width:92px;color:var(--muted);font-family:monospace;font-size:13px;white-space:nowrap;}}
  td.copyable{{cursor:pointer;}} td.copyable:hover{{background:#eef2f3 !important;text-decoration:underline dotted;}}
  .noteBtn{{font-family:"Geeza Pro","Amiri",sans-serif;font-size:12px;border:1px solid var(--line);
     background:#f2f6f7;color:var(--accent2);border-radius:5px;padding:1px 7px;cursor:pointer;margin-right:6px;white-space:nowrap;}}
  .noteBtn:hover{{background:#e3eef1;}}
  .ar-note{{background:#f7f4ee;border-right:3px solid var(--accent2);border-radius:6px;padding:10px 14px;
     font-family:"Geeza Pro","Scheherazade New","Amiri",serif;font-size:16px;line-height:1.9;color:#2a2620;}}
  .empty{{color:var(--muted);font-style:italic;font-size:14px;margin:4px 0 0;}}
  footer{{margin-top:40px;padding-top:16px;border-top:1px solid var(--line);color:var(--muted);font-size:13px;}}
  #toast{{position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:var(--ink);color:#fff;
     padding:8px 18px;border-radius:20px;font-family:sans-serif;font-size:14px;opacity:0;transition:opacity .2s;pointer-events:none;z-index:9;}}
  #toast.show{{opacity:.95;}}
  @media(max-width:640px){{td.rub,th.rub{{display:none}}}}
</style>
</head>
<body>
<div class="wrap">
<header class="top">
  <div>
    <h1>{i18n("Образ ислама в газете «La Croix» — указатель статей","L’image de l’islam dans « La Croix » — index des articles","span")}</h1>
    <div class="sub ar">صورة الإسلام في صحيفة «La Croix» (صحيفة الصليب) ونقدها — فهرس المقالات</div>
  </div>
  <div class="langsw">{i18n("Язык:","Langue :","span")}
    <button id="btn-ru" class="on" onclick="setLang('ru')">RU</button><button id="btn-fr" onclick="setLang('fr')">FR</button>
  </div>
</header>

<div class="meta">
  {i18n("Рабочий указатель статей La Croix по темам исследования (5 глав, 21 тема).","Index de travail des articles de La Croix par thèmes de la recherche (5 chapitres, 21 thèmes).","span")}
  {i18n("Всего статей:","Total d’articles :","span")} <b>{total}</b>. {i18n("С арабскими аннотациями:","Avec résumé en arabe :","span")} <b>{n_ann}</b>. {i18n("Обновлено:","Mis à jour :","span")} <b>{today}</b>.<br>
  {i18n("Клик по автору или дате — копирует значение. Кнопка «ملخص عربي» раскрывает арабскую аннотацию.","Un clic sur l’auteur ou la date copie la valeur. Le bouton « ملخص عربي » déploie le résumé en arabe.","span")}<br>
  {i18n("Подборка предварительная; авторы и аннотации заполняются по мере прочтения статей (часть ссылок старого формата временно недоступна — ошибка 502 на стороне сайта).","Sélection préliminaire ; auteurs et résumés ajoutés au fur et à mesure (certains liens anciens sont momentanément indisponibles — erreur 502 côté site).","span")}
</div>

<nav class="toc"><b>{i18n("Содержание","Sommaire","span")}</b><ul>
{chr(10).join(toc)}
</ul></nav>

{chr(10).join(body)}

<footer>
  {i18n("Источник:","Source :","span")} <a href="https://www.la-croix.com/" target="_blank" rel="noopener">la-croix.com</a>.
  {i18n("Доступ по подписке; полный текст — после входа в аккаунт. Арабские аннотации — аналитические резюме, не дословный перевод.","Accès sur abonnement ; texte intégral après connexion. Les résumés en arabe sont analytiques, non une traduction littérale.","span")}
</footer>
</div>

<div id="toast"></div>
<script>
function setLang(l){{
  document.querySelectorAll('.i18n').forEach(function(e){{ if(e.dataset[l]) e.textContent=e.dataset[l]; }});
  document.documentElement.lang=l;
  document.getElementById('btn-ru').classList.toggle('on', l==='ru');
  document.getElementById('btn-fr').classList.toggle('on', l==='fr');
  try{{ localStorage.setItem('ui_lang', l); }}catch(e){{}}
}}
var toastT;
function toast(msg){{ var t=document.getElementById('toast'); t.textContent=msg; t.classList.add('show');
  clearTimeout(toastT); toastT=setTimeout(function(){{t.classList.remove('show');}},1200); }}
function copyText(txt){{
  if(navigator.clipboard && navigator.clipboard.writeText){{ navigator.clipboard.writeText(txt).then(function(){{}},function(){{fallback(txt);}}); }}
  else fallback(txt);
  function fallback(s){{ var ta=document.createElement('textarea'); ta.value=s; ta.style.position='fixed'; ta.style.opacity=0;
     document.body.appendChild(ta); ta.select(); try{{document.execCommand('copy');}}catch(e){{}} ta.remove(); }}
}}
document.addEventListener('click', function(ev){{
  var c=ev.target.closest('.copyable');
  if(c){{ var v=c.textContent.trim(); if(v && v!=='—'){{ copyText(v); toast((document.documentElement.lang==='fr'?'Copié : ':'Скопировано: ')+v); }} return; }}
  var b=ev.target.closest('.noteBtn');
  if(b){{ var tr=b.closest('tr'); var note=tr.nextElementSibling;
    if(note && note.classList.contains('note')){{ var vis=note.style.display!=='none';
      note.style.display=vis?'none':'table-row'; b.setAttribute('aria-expanded', (!vis).toString()); }} }}
}});
try{{ var sv=localStorage.getItem('ui_lang'); if(sv && sv!=='ru') setLang(sv); }}catch(e){{}}
</script>
</body>
</html>
"""

out_desktop = os.path.join(HERE,"La-Croix-islam-index.html")
with open(out_desktop,"w",encoding="utf-8") as f: f.write(doc)
with open(os.path.join(HERE,"La-Croix-islam-index.html"),"w",encoding="utf-8") as f: f.write(doc)
print("written:", out_desktop)
print("total:", total, "| annotated:", n_ann)
