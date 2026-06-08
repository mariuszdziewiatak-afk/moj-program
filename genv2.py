from __future__ import annotations
from dataclasses import dataclass, field
from typing import List
from pathlib import Path
import json

from PyQt6 import QtWidgets


# -----------------------------
# MODELE DANYCH
# -----------------------------
@dataclass
class Param:
    name: str
    price: float


@dataclass
class ParamGroup:
    name: str
    price: float = 0.0
    params: List[Param] = field(default_factory=list)


@dataclass
class Variant:
    name: str
    param_groups: List[ParamGroup] = field(default_factory=list)


@dataclass
class Section:
    name: str
    variants: List[Variant] = field(default_factory=list)


@dataclass
class DiscountRule:
    # rule_type: "free_shipping", "percent_over_value", "percent_over_qty", "progressive"
    rule_type: str
    value: float       # % lub 0
    threshold: float   # próg kwotowy / ilościowy
    step: float = 0.0  # dla progresywnych (co X zł)


@dataclass
class ConfigModel:
    product_name: str = ""
    sections: List[Section] = field(default_factory=list)
    discount_rules: List[DiscountRule] = field(default_factory=list)


# -----------------------------
# GENERATOR HTML (Material Design + rabaty)
# -----------------------------
def generate_html(model: ConfigModel, output_path: str):
    print(">>> GENERUJĘ NOWY HTML Z RABATAMI <<<")
    product_name = model.product_name
    sections = model.sections

    rules_json = json.dumps(
        [
            {
                "rule_type": r.rule_type,
                "value": r.value,
                "threshold": r.threshold,
                "step": r.step,
            }
            for r in model.discount_rules
        ],
        ensure_ascii=False,
    )

    html = f"""<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="UTF-8">
<title>{product_name}</title>
<style>
/* --- STYL MATERIAL DESIGN --- */
:root {{
    --md-primary: #1d4ed8;
    --md-primary-light: #2563eb;
    --md-primary-soft: #e0ecff;
    --md-bg: #f3f4f6;
    --md-surface: #ffffff;
    --md-border: #e5e7eb;
    --md-text-main: #111827;
    --md-text-muted: #6b7280;
    --md-shadow-soft: 0 10px 30px rgba(15, 23, 42, 0.12);
}}

body {{
    font-family: system-ui, sans-serif;
    background: #eef2ff;
    margin: 0;
    padding: 40px 0;
}}

.wrapper {{
    max-width: 1040px;
    margin: 0 auto;
    padding: 0 16px;
}}

.card {{
    background: var(--md-surface);
    border-radius: 18px;
    padding: 24px 28px;
    box-shadow: var(--md-shadow-soft);
    border: 1px solid rgba(148,163,184,0.25);
}}

h1 {{
    margin-top: 0;
    font-size: 26px;
    display: flex;
    align-items: center;
    gap: 10px;
}}

.badge-main {{
    font-size: 11px;
    padding: 3px 9px;
    border-radius: 999px;
    background: var(--md-primary-soft);
    color: var(--md-primary);
}}

.layout {{
    display: flex;
    gap: 24px;
    align-items: flex-start;
}}

.main-col {{
    flex: 2;
}}

.side-col {{
    flex: 1;
    background: #f9fafb;
    border-radius: 14px;
    border: 1px solid var(--md-border);
    padding: 12px 14px;
    font-size: 13px;
}}

.side-col h3 {{
    margin-top: 0;
    font-size: 14px;
}}

.accordion-item {{
    border-radius: 16px;
    margin-bottom: 12px;
    border: 1px solid var(--md-border);
    background: #fff;
}}

.accordion-header {{
    width: 100%;
    padding: 12px 16px;
    background: #e0ecff;
    border: none;
    font-size: 14px;
    font-weight: 600;
    display: flex;
    justify-content: space-between;
    cursor: pointer;
}}

.accordion-body {{
    display: none;
    padding: 12px 16px;
}}

.variant {{
    margin-top: 10px;
    border-radius: 12px;
    border: 1px solid #d1d5db;
    background: #f9fafb;
}}

.variant-header {{
    width: 100%;
    padding: 9px 12px;
    background: #e5e7eb;
    border: none;
    font-size: 13px;
    font-weight: 600;
    display: flex;
    justify-content: space-between;
    cursor: pointer;
}}

.variant-body {{
    display: none;
    padding: 9px 12px;
}}

.group {{
    margin-top: 8px;
    border-radius: 10px;
    border: 1px dashed #9ca3af;
    background: #f3f4f6;
}}

.group-header {{
    width: 100%;
    padding: 7px 10px;
    background: #e5e7eb;
    border: none;
    font-size: 12px;
    font-weight: 600;
    display: flex;
    justify-content: space-between;
    cursor: pointer;
}}

.group-body {{
    display: none;
    padding: 7px 10px;
}}

.param {{
    margin-top: 5px;
    font-size: 13px;
    display: flex;
    align-items: center;
    gap: 8px;
}}

.param input[type="number"] {{
    width: 60px;
    padding: 3px 5px;
    border-radius: 6px;
    border: 1px solid #d1d5db;
}}

.summary {{
    margin-top: 24px;
    padding-top: 14px;
    border-top: 1px solid #9ca3af;
}}

.price-total {{
    font-size: 18px;
    font-weight: 700;
    color: var(--md-primary);
}}

.price-final {{
    font-size: 20px;
    font-weight: 800;
    color: #16a34a;
}}

.discount-info {{
    margin-top: 8px;
    font-size: 13px;
    color: #16a34a;
}}
</style>
</head>
<body>
<div class="wrapper">
<div class="card">
<h1>{product_name} <span class="badge-main">Konfigurator</span></h1>

<div class="layout">
  <div class="main-col">

<form id="configForm">
<div class="accordion">
"""

    # SEKCJE
    for s_index, section in enumerate(sections):
        html += f"""
<div class="accordion-item">
  <button type="button" class="accordion-header" data-target="sec_{s_index}">
    <span>{section.name}</span>
    <span class="section-count">0</span>
  </button>

  <div class="accordion-body" id="sec_{s_index}">
"""

        # WARIANTY
        for v_index, variant in enumerate(section.variants):
            html += f"""
    <div class="variant">
      <button type="button" class="variant-header" data-target="var_{s_index}_{v_index}">
        <span>Wariant: {variant.name}</span>
        <span class="variant-count">0</span>
      </button>

      <div class="variant-body" id="var_{s_index}_{v_index}">
"""

            # GRUPY
            for g_index, group in enumerate(variant.param_groups):
                html += f"""
        <div class="group">
          <button type="button" class="group-header" data-target="grp_{s_index}_{v_index}_{g_index}">
            <span>{group.name}</span>
            <span class="group-count">0</span>
          </button>

          <div class="group-body" id="grp_{s_index}_{v_index}_{g_index}">
"""

                # PARAMETRY
                for param in group.params:
                    html += f"""
            <div class="param">
              <input type="checkbox" class="paramCheck" data-price="{param.price}">
              <label>{param.name}</label>
              <span>(+{param.price} zł)</span>
              <span>Ilość:</span>
              <input type="number" class="qty" min="1" value="1">
            </div>
"""

                html += """
          </div>
        </div>
"""

            html += """
      </div>
    </div>
"""

        html += """
  </div>
</div>
"""

    # PODSUMOWANIE + PANEL RABATÓW
    html += f"""
</div>

<div class="summary">
  <h3>Podsumowanie</h3>
  <ul id="summaryList"></ul>
  <div>Łączna cena: <span class="price-total" id="totalPrice">0 zł</span></div>
  <div class="discount-info" id="discountInfo"></div>
  <div>Po rabatach: <span class="price-final" id="finalPrice">0 zł</span></div>
</div>

</form>
  </div>

  <div class="side-col">
    <h3>Reguły rabatowe</h3>
    <ul id="rulesList"></ul>
  </div>
</div>

</div>
</div>

<script>
const discountRules = {rules_json};

/* AKORDEONY */
document.querySelectorAll('.accordion-header').forEach(btn => {{
  btn.addEventListener('click', () => {{
    const body = document.getElementById(btn.dataset.target);
    body.style.display = body.style.display === 'block' ? 'none' : 'block';
  }});
}});

document.querySelectorAll('.variant-header').forEach(btn => {{
  btn.addEventListener('click', () => {{
    const body = document.getElementById(btn.dataset.target);
    body.style.display = body.style.display === 'block' ? 'none' : 'block';
  }});
}});

document.querySelectorAll('.group-header').forEach(btn => {{
  btn.addEventListener('click', () => {{
    const body = document.getElementById(btn.dataset.target);
    body.style.display = body.style.display === 'block' ? 'none' : 'block';
  }});
}});

/* LISTA REGUŁ Z BOKU */
function renderRulesSidebar() {{
  const list = document.getElementById("rulesList");
  list.innerHTML = "";
  if (!discountRules || discountRules.length === 0) {{
    const li = document.createElement("li");
    li.textContent = "Brak zdefiniowanych reguł.";
    list.appendChild(li);
    return;
  }}
  discountRules.forEach(r => {{
    const li = document.createElement("li");
    if (r.rule_type === "free_shipping") {{
      li.textContent = "Darmowa dostawa powyżej " + r.threshold + " zł";
    }} else if (r.rule_type === "percent_over_value") {{
      li.textContent = "Rabat " + r.value + "% powyżej " + r.threshold + " zł";
    }} else if (r.rule_type === "percent_over_qty") {{
      li.textContent = "Rabat " + r.value + "% powyżej " + r.threshold + " szt.";
    }} else if (r.rule_type === "progressive") {{
      li.textContent = "Rabat progresywny +" + r.value + "% co " + r.step + " zł (od " + r.threshold + " zł)";
    }} else {{
      li.textContent = "Reguła: " + JSON.stringify(r);
    }}
    list.appendChild(li);
  }});
}}
renderRulesSidebar();
/* OBLICZANIE SUM + RABATY */
function calculateTotals() {{
  let total = 0;
  let totalQty = 0;
  const summary = document.getElementById("summaryList");
  summary.innerHTML = "";

  document.querySelectorAll(".accordion-item").forEach(sectionItem => {{
    const sectionName = sectionItem.querySelector(".accordion-header span").innerText;
    let sectionCount = 0;

    sectionItem.querySelectorAll(".variant").forEach(variant => {{
      const variantName = variant.querySelector(".variant-header span").innerText.replace("Wariant: ", "");
      let variantCount = 0;

      variant.querySelectorAll(".group").forEach(group => {{
        const groupName = group.querySelector(".group-header span").innerText;
        let groupCount = 0;

        group.querySelectorAll(".param").forEach(param => {{
          const checkbox = param.querySelector("input[type='checkbox']");
          const qty = parseInt(param.querySelector(".qty").value);
          const price = parseFloat(checkbox.dataset.price);
          const paramName = param.querySelector("label").innerText;

          if (checkbox.checked && qty > 0) {{
            const lineTotal = price * qty;
            total += lineTotal;
            totalQty += qty;
            groupCount += qty;
            variantCount += qty;
            sectionCount += qty;

            const li = document.createElement("li");
            li.textContent = sectionName + " , " + variantName + " , " + groupName + " , " +
                             paramName + " x" + qty + " = " + lineTotal + " zł";
            summary.appendChild(li);
          }}
        }});

        group.querySelector(".group-count").innerText = groupCount;
      }});

      variant.querySelector(".variant-count").innerText = variantCount;
    }});

    sectionItem.querySelector(".section-count").innerText = sectionCount;
  }});

  let discount = 0;
  let discountMessages = [];

  if (discountRules && discountRules.length > 0) {{
    discountRules.forEach(r => {{
      if (r.rule_type === "free_shipping") {{
        if (total >= r.threshold) {{
          discountMessages.push("Aktywna: darmowa dostawa powyżej " + r.threshold + " zł");
        }}
      }} else if (r.rule_type === "percent_over_value") {{
        if (total >= r.threshold) {{
          const d = total * (r.value / 100.0);
          discount += d;
          discountMessages.push("Aktywny rabat " + r.value + "% powyżej " + r.threshold + " zł (−" + d.toFixed(2) + " zł)");
        }}
      }} else if (r.rule_type === "percent_over_qty") {{
        if (totalQty >= r.threshold) {{
          const d = total * (r.value / 100.0);
          discount += d;
          discountMessages.push("Aktywny rabat " + r.value + "% powyżej " + r.threshold + " szt. (−" + d.toFixed(2) + " zł)");
        }}
      }} else if (r.rule_type === "progressive") {{
        if (total >= r.threshold && r.step > 0) {{
          const steps = Math.floor((total - r.threshold) / r.step) + 1;
          const d = total * (r.value / 100.0) * steps;
          discount += d;
          discountMessages.push("Aktywny rabat progresywny: " + steps + " krok(ów) po " + r.value + "% (łącznie −" + d.toFixed(2) + " zł)");
        }}
      }}
    }});
  }}

  const finalTotal = Math.max(0, total - discount);

  document.getElementById("totalPrice").innerText = total.toFixed(2) + " zł";
  document.getElementById("finalPrice").innerText = finalTotal.toFixed(2) + " zł";

  const di = document.getElementById("discountInfo");
  if (discountMessages.length === 0) {{
    di.textContent = "Brak aktywnych rabatów.";
  }} else {{
    di.innerHTML = discountMessages.join("<br>");
  }}
}}

document.getElementById("configForm").addEventListener("change", calculateTotals);
</script>

</body>
</html>
"""

    Path(output_path).write_text(html, encoding="utf-8")


# -----------------------------
# WCZYTYWANIE Z HTML
# (bez rabatów – HTML ich nie zapisuje)
# -----------------------------
def load_from_html(path: str) -> ConfigModel:
    from bs4 import BeautifulSoup
    html = Path(path).read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")

    model = ConfigModel()

    # Produkt
    h1 = soup.find("h1")
    if h1:
        model.product_name = h1.text.replace("Konfigurator", "").strip()

    # Sekcje
    for sec in soup.select(".accordion-item"):
        el = sec.select_one(".accordion-header span:first-child")
        sec_name = el.text.strip() if el else "Sekcja"
        section = Section(name=sec_name)

        # Warianty
        for var in sec.select(".variant"):
            el = var.select_one(".variant-header span:first-child")
            vname = el.text.replace("Wariant:", "").strip() if el else "Wariant"
            variant = Variant(name=vname)

            # Grupy
            for grp in var.select(".group"):
                el = grp.select_one(".group-header span:first-child")
                gname = el.text.strip() if el else "Grupa"
                group = ParamGroup(name=gname)

                # Parametry
                for prm in grp.select(".param"):
                    pname = prm.select_one("label").text.strip()

                    price_span = prm.select_one("span")
                    if price_span:
                        ptxt = price_span.text
                        ptxt = (
                            ptxt.replace("(", "")
                                .replace(")", "")
                                .replace("+", "")
                                .replace("zł", "")
                                .replace(" ", "")
                                .strip()
                        )
                        try:
                            pprice = float(ptxt)
                        except:
                            pprice = 0.0
                    else:
                        pprice = 0.0

                    group.params.append(Param(name=pname, price=pprice))

                variant.param_groups.append(group)

            section.variants.append(variant)

        model.sections.append(section)

    # rabaty z HTML nie są odtwarzane – zostają puste
    model.discount_rules = []
    return model


# -----------------------------
# DIALOGI POMOCNICZE
# -----------------------------
class TextInputDialog(QtWidgets.QDialog):
    def __init__(self, title: str, label: str, parent=None, default: str = ""):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.value = None

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel(label))
        self.edit = QtWidgets.QLineEdit(self)
        self.edit.setText(default)
        layout.addWidget(self.edit)

        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def accept(self):
        text = self.edit.text().strip()
        if not text:
            QtWidgets.QMessageBox.warning(self, "Błąd", "Pole nie może być puste.")
            return
        self.value = text
        super().accept()


class ParamDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, default_name="", default_price=0.0):
        super().__init__(parent)
        self.setWindowTitle("Parametr")
        self.param = None

        layout = QtWidgets.QFormLayout(self)

        self.name_edit = QtWidgets.QLineEdit(self)
        self.name_edit.setText(default_name)
        layout.addRow("Nazwa parametru:", self.name_edit)

        self.price_edit = QtWidgets.QLineEdit(self)
        self.price_edit.setText(str(default_price))
        layout.addRow("Cena:", self.price_edit)

        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

    def accept(self):
        name = self.name_edit.text().strip()
        if not name:
            QtWidgets.QMessageBox.warning(self, "Błąd", "Nazwa nie może być pusta.")
            return
        try:
            price = float(self.price_edit.text().replace(",", "."))
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Błąd", "Cena musi być liczbą.")
            return
        self.param = Param(name=name, price=price)
        super().accept()


class GroupDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, default_name="", default_price=0.0):
        super().__init__(parent)
        self.setWindowTitle("Grupa parametrów")
        self.group_name = None
        self.group_price = 0.0

        layout = QtWidgets.QFormLayout(self)

        self.name_edit = QtWidgets.QLineEdit(self)
        self.name_edit.setText(default_name)
        layout.addRow("Nazwa grupy:", self.name_edit)

        self.price_edit = QtWidgets.QLineEdit(self)
        self.price_edit.setText(str(default_price))
        layout.addRow("Cena grupy:", self.price_edit)

        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

    def accept(self):
        name = self.name_edit.text().strip()
        if not name:
            QtWidgets.QMessageBox.warning(self, "Błąd", "Nazwa nie może być pusta.")
            return
        price_text = self.price_edit.text().strip()
        try:
            price = float(price_text.replace(",", ".")) if price_text else 0.0
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Błąd", "Cena musi być liczbą.")
            return
        self.group_name = name
        self.group_price = price
        super().accept()


# -----------------------------
# DIALOG REGUŁ RABATOWYCH
# -----------------------------
class RuleDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, rule: DiscountRule | None = None):
        super().__init__(parent)
        self.setWindowTitle("Reguła rabatowa")
        self.rule = None

        layout = QtWidgets.QFormLayout(self)

        self.type_combo = QtWidgets.QComboBox(self)
        self.type_combo.addItems([
            "Darmowa dostawa powyżej kwoty",
            "Rabat % powyżej kwoty",
            "Rabat % powyżej ilości",
            "Rabat progresywny"
        ])
        layout.addRow("Typ reguły:", self.type_combo)

        self.value_edit = QtWidgets.QLineEdit(self)
        layout.addRow("Wartość (%):", self.value_edit)

        self.threshold_edit = QtWidgets.QLineEdit(self)
        layout.addRow("Próg:", self.threshold_edit)

        self.step_edit = QtWidgets.QLineEdit(self)
        layout.addRow("Krok (progresywny):", self.step_edit)

        if rule:
            mapping = {
                "free_shipping": 0,
                "percent_over_value": 1,
                "percent_over_qty": 2,
                "progressive": 3,
            }
            self.type_combo.setCurrentIndex(mapping.get(rule.rule_type, 0))
            self.value_edit.setText(str(rule.value))
            self.threshold_edit.setText(str(rule.threshold))
            self.step_edit.setText(str(rule.step))

        btns = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.StandardButton.Ok |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addRow(btns)

    def accept(self):
        idx = self.type_combo.currentIndex()
        if idx == 0:
            rule_type = "free_shipping"
        elif idx == 1:
            rule_type = "percent_over_value"
        elif idx == 2:
            rule_type = "percent_over_qty"
        else:
            rule_type = "progressive"

        try:
            value = float(self.value_edit.text().replace(",", ".")) if self.value_edit.text() else 0.0
            threshold = float(self.threshold_edit.text().replace(",", ".")) if self.threshold_edit.text() else 0.0
            step = float(self.step_edit.text().replace(",", ".")) if self.step_edit.text() else 0.0
        except ValueError:
            QtWidgets.QMessageBox.warning(self, "Błąd", "Wszystkie pola muszą być liczbami.")
            return

        self.rule = DiscountRule(
            rule_type=rule_type,
            value=value,
            threshold=threshold,
            step=step
        )
        super().accept()
# -----------------------------
# STRONY KREATORA
# -----------------------------
class ProductPage(QtWidgets.QWizardPage):
    def __init__(self, model: ConfigModel):
        super().__init__()
        self.model = model
        self.setTitle("Produkt")

        layout = QtWidgets.QVBoxLayout(self)

        self.load_btn = QtWidgets.QPushButton("Wczytaj konfigurator HTML")
        layout.addWidget(self.load_btn)

        layout.addWidget(QtWidgets.QLabel("Nazwa produktu:"))
        self.name_edit = QtWidgets.QLineEdit(self)
        layout.addWidget(self.name_edit)

        self.load_btn.clicked.connect(self.load_html)

    def initializePage(self):
        if self.model.product_name:
            self.name_edit.setText(self.model.product_name)

    def validatePage(self):
        name = self.name_edit.text().strip()
        if not name:
            QtWidgets.QMessageBox.warning(self, "Błąd", "Podaj nazwę produktu.")
            return False
        self.model.product_name = name
        return True

    def load_html(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Wczytaj HTML", filter="Pliki HTML (*.html)"
        )
        if not path:
            return
        try:
            new_model = load_from_html(path)
            wizard = self.wizard()
            wizard.model = new_model
            wizard.product_page.model = new_model
            wizard.sections_page.model = new_model
            wizard.variants_page.model = new_model
            wizard.groups_page.model = new_model
            wizard.params_page.model = new_model
            wizard.rules_page.model = new_model
            wizard.summary_page.model = new_model
            self.name_edit.setText(new_model.product_name)
            QtWidgets.QMessageBox.information(self, "OK", "Wczytano konfigurator.")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Błąd", str(e))


class SectionsPage(QtWidgets.QWizardPage):
    def __init__(self, model: ConfigModel):
        super().__init__()
        self.model = model
        self.setTitle("Sekcje")

        layout = QtWidgets.QVBoxLayout(self)

        self.list = QtWidgets.QListWidget(self)
        layout.addWidget(self.list)

        btns = QtWidgets.QHBoxLayout()
        self.add_btn = QtWidgets.QPushButton("Dodaj")
        self.edit_btn = QtWidgets.QPushButton("Edytuj")
        self.del_btn = QtWidgets.QPushButton("Usuń")
        btns.addWidget(self.add_btn)
        btns.addWidget(self.edit_btn)
        btns.addWidget(self.del_btn)
        layout.addLayout(btns)

        self.add_btn.clicked.connect(self.add_section)
        self.edit_btn.clicked.connect(self.edit_section)
        self.del_btn.clicked.connect(self.del_section)

    def initializePage(self):
        self.refresh()

    def refresh(self):
        self.list.clear()
        for s in self.model.sections:
            self.list.addItem(s.name)

    def add_section(self):
        dlg = TextInputDialog("Nowa sekcja", "Nazwa:", self)
        if dlg.exec():
            self.model.sections.append(Section(name=dlg.value))
            self.refresh()

    def edit_section(self):
        row = self.list.currentRow()
        if row < 0:
            return
        sec = self.model.sections[row]
        dlg = TextInputDialog("Edytuj sekcję", "Nazwa:", self, sec.name)
        if dlg.exec():
            sec.name = dlg.value
            self.refresh()

    def del_section(self):
        row = self.list.currentRow()
        if row < 0:
            return
        del self.model.sections[row]
        self.refresh()

    def validatePage(self):
        return len(self.model.sections) > 0


class VariantsPage(QtWidgets.QWizardPage):
    def __init__(self, model: ConfigModel):
        super().__init__()
        self.model = model
        self.setTitle("Warianty")

        layout = QtWidgets.QVBoxLayout(self)

        self.section_combo = QtWidgets.QComboBox(self)
        self.section_combo.currentIndexChanged.connect(self.refresh_variants)
        layout.addWidget(self.section_combo)

        self.list = QtWidgets.QListWidget(self)
        layout.addWidget(self.list)

        btns = QtWidgets.QHBoxLayout()
        self.add_btn = QtWidgets.QPushButton("Dodaj")
        self.edit_btn = QtWidgets.QPushButton("Edytuj")
        self.del_btn = QtWidgets.QPushButton("Usuń")
        btns.addWidget(self.add_btn)
        btns.addWidget(self.edit_btn)
        btns.addWidget(self.del_btn)
        layout.addLayout(btns)

        self.add_btn.clicked.connect(self.add_variant)
        self.edit_btn.clicked.connect(self.edit_variant)
        self.del_btn.clicked.connect(self.del_variant)

    def initializePage(self):
        self.section_combo.clear()
        for s in self.model.sections:
            self.section_combo.addItem(s.name)
        self.refresh_variants()

    def current_section(self):
        idx = self.section_combo.currentIndex()
        return self.model.sections[idx] if idx >= 0 else None

    def refresh_variants(self):
        self.list.clear()
        sec = self.current_section()
        if not sec:
            return
        for v in sec.variants:
            self.list.addItem(v.name)

    def add_variant(self):
        sec = self.current_section()
        if not sec:
            return
        dlg = TextInputDialog("Nowy wariant", "Nazwa:", self)
        if dlg.exec():
            sec.variants.append(Variant(name=dlg.value))
            self.refresh_variants()

    def edit_variant(self):
        sec = self.current_section()
        if not sec:
            return
        row = self.list.currentRow()
        if row < 0:
            return
        var = sec.variants[row]
        dlg = TextInputDialog("Edytuj wariant", "Nazwa:", self, var.name)
        if dlg.exec():
            var.name = dlg.value
            self.refresh_variants()

    def del_variant(self):
        sec = self.current_section()
        if not sec:
            return
        row = self.list.currentRow()
        if row < 0:
            return
        del sec.variants[row]
        self.refresh_variants()


class GroupsPage(QtWidgets.QWizardPage):
    def __init__(self, model: ConfigModel):
        super().__init__()
        self.model = model
        self.setTitle("Grupy parametrów")

        layout = QtWidgets.QVBoxLayout(self)

        self.section_combo = QtWidgets.QComboBox(self)
        self.section_combo.currentIndexChanged.connect(self.refresh_variants)
        layout.addWidget(self.section_combo)

        self.variant_combo = QtWidgets.QComboBox(self)
        self.variant_combo.currentIndexChanged.connect(self.refresh_groups)
        layout.addWidget(self.variant_combo)

        self.list = QtWidgets.QListWidget(self)
        layout.addWidget(self.list)

        btns = QtWidgets.QHBoxLayout()
        self.add_btn = QtWidgets.QPushButton("Dodaj")
        self.edit_btn = QtWidgets.QPushButton("Edytuj")
        self.del_btn = QtWidgets.QPushButton("Usuń")
        btns.addWidget(self.add_btn)
        btns.addWidget(self.edit_btn)
        btns.addWidget(self.del_btn)
        layout.addLayout(btns)

        self.add_btn.clicked.connect(self.add_group)
        self.edit_btn.clicked.connect(self.edit_group)
        self.del_btn.clicked.connect(self.del_group)

    def initializePage(self):
        self.section_combo.clear()
        for s in self.model.sections:
            self.section_combo.addItem(s.name)
        self.refresh_variants()

    def current_section(self):
        idx = self.section_combo.currentIndex()
        return self.model.sections[idx] if idx >= 0 else None

    def current_variant(self):
        sec = self.current_section()
        if not sec:
            return None
        idx = self.variant_combo.currentIndex()
        return sec.variants[idx] if idx >= 0 else None

    def refresh_variants(self):
        self.variant_combo.clear()
        sec = self.current_section()
        if not sec:
            return
        for v in sec.variants:
            self.variant_combo.addItem(v.name)
        self.refresh_groups()

    def refresh_groups(self):
        self.list.clear()
        var = self.current_variant()
        if not var:
            return
        for g in var.param_groups:
            label = g.name
            if g.price:
                label += f" (+{g.price} zł)"
            self.list.addItem(label)

    def add_group(self):
        var = self.current_variant()
        if not var:
            return
        dlg = GroupDialog(self)
        if dlg.exec():
            var.param_groups.append(ParamGroup(name=dlg.group_name, price=dlg.group_price))
            self.refresh_groups()

    def edit_group(self):
        var = self.current_variant()
        if not var:
            return
        row = self.list.currentRow()
        if row < 0:
            return
        grp = var.param_groups[row]
        dlg = GroupDialog(self, grp.name, grp.price)
        if dlg.exec():
            grp.name = dlg.group_name
            grp.price = dlg.group_price
            self.refresh_groups()

    def del_group(self):
        var = self.current_variant()
        if not var:
            return
        row = self.list.currentRow()
        if row < 0:
            return
        del var.param_groups[row]
        self.refresh_groups()


class ParamsPage(QtWidgets.QWizardPage):
    def __init__(self, model: ConfigModel):
        super().__init__()
        self.model = model
        self.setTitle("Parametry")

        layout = QtWidgets.QVBoxLayout(self)

        self.section_combo = QtWidgets.QComboBox(self)
        self.section_combo.currentIndexChanged.connect(self.refresh_variants)
        layout.addWidget(self.section_combo)

        self.variant_combo = QtWidgets.QComboBox(self)
        self.variant_combo.currentIndexChanged.connect(self.refresh_groups)
        layout.addWidget(self.variant_combo)

        self.group_combo = QtWidgets.QComboBox(self)
        self.group_combo.currentIndexChanged.connect(self.refresh_params)
        layout.addWidget(self.group_combo)

        self.list = QtWidgets.QListWidget(self)
        layout.addWidget(self.list)

        btns = QtWidgets.QHBoxLayout()
        self.add_btn = QtWidgets.QPushButton("Dodaj")
        self.edit_btn = QtWidgets.QPushButton("Edytuj")
        self.del_btn = QtWidgets.QPushButton("Usuń")
        btns.addWidget(self.add_btn)
        btns.addWidget(self.edit_btn)
        btns.addWidget(self.del_btn)
        layout.addLayout(btns)

        self.add_btn.clicked.connect(self.add_param)
        self.edit_btn.clicked.connect(self.edit_param)
        self.del_btn.clicked.connect(self.del_param)

    def initializePage(self):
        self.section_combo.clear()
        for s in self.model.sections:
            self.section_combo.addItem(s.name)
        self.refresh_variants()

    def current_section(self):
        idx = self.section_combo.currentIndex()
        return self.model.sections[idx] if idx >= 0 else None

    def current_variant(self):
        sec = self.current_section()
        if not sec:
            return None
        idx = self.variant_combo.currentIndex()
        return sec.variants[idx] if idx >= 0 else None

    def current_group(self):
        var = self.current_variant()
        if not var:
            return None
        idx = self.group_combo.currentIndex()
        return var.param_groups[idx] if idx >= 0 else None

    def refresh_variants(self):
        self.variant_combo.clear()
        sec = self.current_section()
        if not sec:
            return
        for v in sec.variants:
            self.variant_combo.addItem(v.name)
        self.refresh_groups()

    def refresh_groups(self):
        self.group_combo.clear()
        var = self.current_variant()
        if not var:
            return
        for g in var.param_groups:
            label = g.name
            if g.price:
                label += f" (+{g.price} zł)"
            self.group_combo.addItem(label)
        self.refresh_params()

    def refresh_params(self):
        self.list.clear()
        grp = self.current_group()
        if not grp:
            return
        for p in grp.params:
            self.list.addItem(f"{p.name} (+{p.price} zł)")

    def add_param(self):
        grp = self.current_group()
        if not grp:
            return
        dlg = ParamDialog(self)
        if dlg.exec():
            grp.params.append(dlg.param)
            self.refresh_params()

    def edit_param(self):
        grp = self.current_group()
        if not grp:
            return
        row = self.list.currentRow()
        if row < 0:
            return
        p = grp.params[row]
        dlg = ParamDialog(self, p.name, p.price)
        if dlg.exec():
            grp.params[row] = dlg.param
            self.refresh_params()

    def del_param(self):
        grp = self.current_group()
        if not grp:
            return
        row = self.list.currentRow()
        if row < 0:
            return
        del grp.params[row]
        self.refresh_params()


# -----------------------------
# STRONA REGUŁ RABATOWYCH
# -----------------------------
class RulesPage(QtWidgets.QWizardPage):
    def __init__(self, model: ConfigModel):
        super().__init__()
        self.model = model
        self.setTitle("Reguły rabatowe")

        layout = QtWidgets.QVBoxLayout(self)

        self.list = QtWidgets.QListWidget(self)
        layout.addWidget(self.list)

        btns = QtWidgets.QHBoxLayout()
        self.add_btn = QtWidgets.QPushButton("Dodaj")
        self.edit_btn = QtWidgets.QPushButton("Edytuj")
        self.del_btn = QtWidgets.QPushButton("Usuń")
        btns.addWidget(self.add_btn)
        btns.addWidget(self.edit_btn)
        btns.addWidget(self.del_btn)
        layout.addLayout(btns)

        self.add_btn.clicked.connect(self.add_rule)
        self.edit_btn.clicked.connect(self.edit_rule)
        self.del_btn.clicked.connect(self.del_rule)

    def initializePage(self):
        self.refresh()

    def refresh(self):
        self.list.clear()
        for r in self.model.discount_rules:
            if r.rule_type == "free_shipping":
                txt = f"Darmowa dostawa powyżej {r.threshold} zł"
            elif r.rule_type == "percent_over_value":
                txt = f"Rabat {r.value}% powyżej {r.threshold} zł"
            elif r.rule_type == "percent_over_qty":
                txt = f"Rabat {r.value}% powyżej {r.threshold} szt."
            else:
                txt = f"Progresywny +{r.value}% co {r.step} zł (od {r.threshold} zł)"
            self.list.addItem(txt)

    def add_rule(self):
        dlg = RuleDialog(self)
        if dlg.exec() and dlg.rule:
            self.model.discount_rules.append(dlg.rule)
            self.refresh()

    def edit_rule(self):
        row = self.list.currentRow()
        if row < 0:
            return
        dlg = RuleDialog(self, self.model.discount_rules[row])
        if dlg.exec() and dlg.rule:
            self.model.discount_rules[row] = dlg.rule
            self.refresh()

    def del_rule(self):
        row = self.list.currentRow()
        if row < 0:
            return
        del self.model.discount_rules[row]
        self.refresh()


# -----------------------------
# SUMMARY PAGE
# -----------------------------
class SummaryPage(QtWidgets.QWizardPage):
    def __init__(self, model: ConfigModel):
        super().__init__()
        self.model = model
        self.setTitle("Podsumowanie")

        layout = QtWidgets.QVBoxLayout(self)

        self.text = QtWidgets.QTextEdit(self)
        self.text.setReadOnly(True)
        layout.addWidget(self.text)

        self.save_btn = QtWidgets.QPushButton("Zapisz HTML")
        layout.addWidget(self.save_btn)

        self.save_btn.clicked.connect(self.save_html)

    def initializePage(self):
        lines = []
        lines.append(f"Produkt: {self.model.product_name}")
        for s in self.model.sections:
            lines.append(f"Sekcja: {s.name}")
            for v in s.variants:
                lines.append(f"  Wariant: {v.name}")
                for g in v.param_groups:
                    if g.price:
                        lines.append(f"    Grupa: {g.name} (+{g.price} zł)")
                    else:
                        lines.append(f"    Grupa: {g.name}")
                    for p in g.params:
                        lines.append(f"      Parametr: {p.name} (+{p.price} zł)")

        if self.model.discount_rules:
            lines.append("")
            lines.append("Reguły rabatowe:")
            for r in self.model.discount_rules:
                if r.rule_type == "free_shipping":
                    lines.append(f"  - Darmowa dostawa powyżej {r.threshold} zł")
                elif r.rule_type == "percent_over_value":
                    lines.append(f"  - Rabat {r.value}% powyżej {r.threshold} zł")
                elif r.rule_type == "percent_over_qty":
                    lines.append(f"  - Rabat {r.value}% powyżej {r.threshold} szt.")
                else:
                    lines.append(f"  - Progresywny +{r.value}% co {r.step} zł (od {r.threshold} zł)")

        self.text.setPlainText("\n".join(lines))

    def save_html(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Zapisz jako HTML",
            filter="Pliki HTML (*.html);;Wszystkie pliki (*.*)"
        )
        if not path:
            return
        try:
            generate_html(self.model, path)
            QtWidgets.QMessageBox.information(self, "OK", f"Zapisano plik HTML:\n{path}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Błąd", f"Nie udało się zapisać pliku:\n{e}")
        print(">>> ZAPISUJĘ DO:", path)

# -----------------------------
# GŁÓWNY KREATOR
# -----------------------------
class ConfigWizard(QtWidgets.QWizard):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kreator konfiguratora produktu (PyQt6)")

        self.model = ConfigModel()

        self.setOption(QtWidgets.QWizard.WizardOption.NoBackButtonOnStartPage, True)

        self.product_page = ProductPage(self.model)
        self.sections_page = SectionsPage(self.model)
        self.variants_page = VariantsPage(self.model)
        self.groups_page = GroupsPage(self.model)
        self.params_page = ParamsPage(self.model)
        self.rules_page = RulesPage(self.model)
        self.summary_page = SummaryPage(self.model)

        self.addPage(self.product_page)
        self.addPage(self.sections_page)
        self.addPage(self.variants_page)
        self.addPage(self.groups_page)
        self.addPage(self.params_page)
        self.addPage(self.rules_page)
        self.addPage(self.summary_page)


# -----------------------------
# START APLIKACJI
# -----------------------------
def main():
    import sys
    app = QtWidgets.QApplication(sys.argv)
    wizard = ConfigWizard()
    wizard.resize(900, 650)
    wizard.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
