from django.urls import path
from dashboard import views

app_name = "dashboard"

urlpatterns = [
    path("", views.DashboardHomeView.as_view(), name="home"),

    # Store selection
    path("store/<int:store_id>/select/", views.SelectStoreView.as_view(), name="select-store"),

    # Products
    path("products/", views.ProductListView.as_view(), name="product-list"),
    path("products/add/", views.ProductCreateView.as_view(), name="product-create"),
    path("products/<int:pk>/edit/", views.ProductEditView.as_view(), name="product-edit"),
    path("products/<int:pk>/images/", views.ProductImagesView.as_view(), name="product-images"),
    path("products/<int:pk>/images/reorder/", views.ProductImageReorderView.as_view(), name="product-image-reorder"),
    path("products/<int:pk>/images/<int:image_id>/delete/", views.ProductImageDeleteView.as_view(), name="product-image-delete"),
    path("products/<int:pk>/images/<int:image_id>/set-primary/", views.ProductImageSetPrimaryView.as_view(), name="product-image-set-primary"),
    path("products/bulk-action/", views.ProductBulkActionView.as_view(), name="product-bulk-action"),

    # Categories
    path("categories/", views.CategoryListView.as_view(), name="category-list"),
    path("categories/add/", views.CategoryCreateView.as_view(), name="category-create"),

    # Warehouses (Sprint 4 — SO-50, SO-51, SS-13)
    path("warehouses/", views.WarehouseListView.as_view(), name="warehouse-list"),
    path("warehouses/add/", views.WarehouseCreateView.as_view(), name="warehouse-add"),
    path("warehouses/<int:pk>/edit/", views.WarehouseEditView.as_view(), name="warehouse-edit"),
    path("warehouses/<int:pk>/inventory/", views.WarehouseInventoryView.as_view(), name="warehouse-inventory"),
    path("warehouses/transfer/", views.StockTransferView.as_view(), name="stock-transfer"),
    path("warehouses/staff/", views.StaffWarehouseAssignmentView.as_view(), name="staff-warehouses"),

    # Orders
    path("orders/", views.OrderListView.as_view(), name="order-list"),
    path("orders/<int:pk>/", views.OrderDetailView.as_view(), name="order-detail"),

    # Accounting
    path("accounting/", views.AccountingLedgerView.as_view(), name="accounting-ledger"),

    # Settings
    path("settings/", views.StoreSettingsView.as_view(), name="store-settings"),

    # Theme
    path("theme/", views.ThemeSelectView.as_view(), name="theme-select"),
    path("theme/customize/", views.ThemeCustomizeView.as_view(), name="theme-customize"),
    path("theme/custom-css/", views.ThemeCustomCSSView.as_view(), name="theme-custom-css"),

    # SO-46: Block page editor
    path("pages/edit/", views.PageEditorView.as_view(), name="page-editor"),
    path("pages/publish/", views.PagePublishView.as_view(), name="page-publish"),
    path("pages/rollback/", views.PageRollbackView.as_view(), name="page-rollback"),
]
