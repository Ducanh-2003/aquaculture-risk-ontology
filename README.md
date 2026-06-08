# AQUA-RISK — Hệ thống Cảnh báo Sớm Dịch bệnh Thủy sản

**Nguyễn Đức Anh**
**MSSV:** 64130053
**Trường Đại học Nha Trang**

---

# Cài đặt

Cài đặt các thư viện Python cần thiết:

```bash
pip install pandas numpy matplotlib joblib scikit-learn xgboost rdflib pyshacl streamlit plotly
```

Ngoài ra cần cài đặt:

* Protégé 5.6.x
* Pellet Reasoner Plugin

Tải tại:

https://protege.stanford.edu

---

# Chạy Pipeline

Pipeline được thực hiện theo các bước sau.
**Lưu ý:** Bước 3 là bước thủ công và bắt buộc.

## Bước 1 — Chạy `main.ipynb` từ Cell 1 đến Cell 4

Cell 1 sẽ tự động tải dữ liệu từ GitHub (yêu cầu kết nối Internet).

Sau khi hoàn thành Cell 4, hệ thống sẽ sinh ra file:

```text
aqua_kg_multiPond.ttl
```

---

## Bước 2 — Chạy SHACL Validation (Tùy chọn)

```bash
python shacl.py
```

Bước này dùng để kiểm tra chất lượng dữ liệu bằng các ràng buộc SHACL.

---

## Bước 3 — Chạy Pellet Reasoner trong Protégé (Thủ công)

### Mở Ontology

```text
Protégé → File → Open
```

Chọn file:

```text
aqua_kg_multiPond.ttl
```

### Chạy Reasoner

```text
Reasoner → Pellet → Start Reasoner
```

### Xuất Ontology sau suy diễn

```text
File → Save inferred ontology as...
```

Thông tin lưu:

* Tên file: `aqua_inferred.ttl`
* Định dạng: Turtle (.ttl)
* Thư mục lưu: cùng thư mục với `main.ipynb`


---

## Bước 4 — Chạy `main.ipynb` từ Cell 5 đến Cell 9

Sau khi hoàn thành sẽ sinh ra:

* Dataset_Mocked_MultiPond.csv
* best_classifier_model.pkl
* best_regressor_model.pkl
* classifier_features.pkl
* regressor_features.pkl

---

## Bước 5 — Chạy Dashboard

```bash
streamlit run dashboard.py
```

Mở trình duyệt tại:

```text
http://localhost:8501
```

---

# Các File Đầu Ra

| File                           | Sinh bởi                  |
| ------------------------------ | ------------------------- |
| `aqua_kg_multiPond.ttl`        | Cell 4                    |
| `aqua_inferred.ttl`            | Protégé + Pellet Reasoner |
| `Dataset_Mocked_MultiPond.csv` | Cell 6                    |
| `best_classifier_model.pkl`    | Cell 8                    |
| `best_regressor_model.pkl`     | Cell 9                    |
| `classifier_features.pkl`      | Cell 8                    |
| `regressor_features.pkl`       | Cell 9                    |

---

# Cấu trúc Pipeline

```text
Raw Data
    │
    ▼
Cell 1–4
    │
    ▼
aqua_kg_multiPond.ttl
    │
    ▼
Protégé + Pellet
    │
    ▼
aqua_inferred.ttl
    │
    ▼
Cell 5–9
    │
    ├── Dataset_Mocked_MultiPond.csv
    ├── best_classifier_model.pkl
    ├── best_regressor_model.pkl
    ├── classifier_features.pkl
    └── regressor_features.pkl
    │
    ▼
dashboard.py
```
