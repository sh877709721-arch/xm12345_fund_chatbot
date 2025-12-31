import { DataTable } from "@/components/admin/knowledge/knowledge-table";
import { KnowledgeCatalogComp } from "@/components/admin/knowledge/knowledge-catalog";
import { useKnowledgeData } from "@/hooks/use-knowledge-data";

export default function KnowledgeListPage() {
  const {
    knowledgeData,
    catalogs,
    catalogTree,
    selectedCatalog,
    searchParams,
    loading,
    catalogsLoading,
    handleCatalogSelect,
    handleSearch,
    handleReset,
    handlePageChange,
    handlePageSizeChange,
    refreshCatalogs,
    updateLocalKnowledgeEntry,
  } = useKnowledgeData();

  return (
    <div className="flex gap-2 h-full">
      {/* 左侧目录树 */}
      <div className="w-1/6 min-w-[200px] max-h-[540px] flex flex-col">
        <KnowledgeCatalogComp
          catalogTree={catalogTree}
          catalogs={catalogs}
          loading={catalogsLoading}
          onCatalogSelect={handleCatalogSelect}
          onCatalogRefresh={refreshCatalogs}
        />
      </div>
      {/* 右侧表格区域 */}
      <div className="flex-1 flex flex-col h-full">
        <DataTable
          data={knowledgeData.items}
          pagination={{
            total: knowledgeData.total,
            page: knowledgeData.page,
            size: knowledgeData.size,
            hasNext: knowledgeData.has_next,
            hasPrev: knowledgeData.has_prev,
          }}
          selectedCatalog={selectedCatalog}
          loading={loading}
          searchParams={searchParams}
          onSearch={handleSearch}
          onReset={handleReset}
          onPageChange={handlePageChange}
          onPageSizeChange={handlePageSizeChange}
          onUpdateLocal={updateLocalKnowledgeEntry}
        />
      </div>
    </div>
  );
}
