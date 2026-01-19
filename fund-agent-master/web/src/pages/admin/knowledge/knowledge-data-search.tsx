import { useState } from "react";
import { searchDataTable } from "@/utils/request/search";
import type {
	DataTableSearchRequest,
	DataTableSearchResult
} from "@/utils/request/search";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Loader2, Search, FileText, Database } from "lucide-react";
import { cn } from "@/lib/utils";

export default function KnowledgeDataSearch() {
	const [query, setQuery] = useState("");
	const [searchResults, setSearchResults] = useState<DataTableSearchResult[]>([]);
	const [selectedResult, setSelectedResult] = useState<DataTableSearchResult | null>(null);
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);

	const handleSearch = async () => {
		if (!query.trim()) return;

		setLoading(true);
		setError(null);
		setSelectedResult(null);

		try {
			const params: DataTableSearchRequest = {
				query: query.trim(),
				top_n: 10,
				threshold: 0.7
			};

			const data = await searchDataTable(params);

			if (data) {
				setSearchResults(data.results);
				// 自动选中第一个结果
				if (data.results.length > 0) {
					setSelectedResult(data.results[0]);
				}
			} else {
				setError("搜索失败，请重试");
			}
		} catch (err) {
			setError("搜索失败，请重试");
			console.error(err);
		} finally {
			setLoading(false);
		}
	};

	const handleKeyPress = (e: React.KeyboardEvent) => {
		if (e.key === "Enter") {
			handleSearch();
		}
	};

	// 渲染表格行数据
	const renderTableRow = (rowData: Record<string, any>) => {
		return (
			<div className="grid grid-cols-2 gap-1.5">
				{Object.entries(rowData).map(([key, value]) => (
					<div key={key} className="flex items-start gap-2 text-xs">
						<Badge variant="outline" className="text-xs whitespace-nowrap shrink-0">
							{key}
						</Badge>
						<span className="text-xs break-all flex-1">{String(value)}</span>
					</div>
				))}
			</div>
		);
	};

	return (
		<div className="p-6 space-y-6">
			{/* 搜索框 */}
			<div className="flex gap-2">
				<Input
					placeholder="请输入搜索关键词"
					value={query}
					onChange={(e) => setQuery(e.target.value)}
					onKeyDown={handleKeyPress}
					className="flex-1"
				/>
				<Button
					onClick={handleSearch}
					disabled={loading || !query.trim()}
					className="px-6"
				>
					{loading ? (
						<Loader2 className="w-4 h-4 animate-spin" />
					) : (
						<Search className="w-4 h-4" />
					)}
					<span className="ml-2">搜索</span>
				</Button>
			</div>

			{/* 错误提示 */}
			{error && (
				<div className="bg-red-50 border border-red-200 rounded-lg p-4">
					<p className="text-red-600 text-sm">{error}</p>
				</div>
			)}

			{/* 主内容区域：左右分栏布局 */}
			{searchResults.length > 0 && (
				<div className="grid grid-cols-1 lg:grid-cols-2 gap-6 h-[calc(100vh-200px)]">
					{/* 左侧：搜索结果列表 */}
					<div className="space-y-3 overflow-hidden flex flex-col">
						<div className="flex items-center gap-2 pb-2">
							<Database className="w-5 h-5 text-muted-foreground" />
							<h3 className="text-lg font-semibold">表格记录</h3>
							<Badge variant="secondary">{searchResults.length} 条结果</Badge>
						</div>

						<div className="flex-1 h-full overflow-y-auto p-2">
							<div className="grid grid-cols-1 gap-3">
								{searchResults.map((result, index) => (
									<Card
										key={result.table_data.knowledge_data_id}
										className={cn(
											"cursor-pointer transition-all hover:shadow-md",
											selectedResult?.table_data.knowledge_data_id ===
											result.table_data.knowledge_data_id &&
											"ring-2 ring-primary"
										)}
										onClick={() => setSelectedResult(result)}
									>
										<CardHeader className="pb-3">
											<div className="flex items-start justify-between">
												<CardTitle className="text-base font-medium">
													记录 #{index + 1}
												</CardTitle>
												<Badge
													variant={result.table_data.score > 0.8 ? "default" : "secondary"}
													className="text-xs"
												>
													相似度: {result.table_data.score.toFixed(2)}
												</Badge>
											</div>
										</CardHeader>
										<CardContent className="pt-0">
											{renderTableRow(result.table_data.row)}
										</CardContent>
									</Card>
								))}
							</div>
						</div>
					</div>

					{/* 右侧：知识库详情 */}
					<div className="space-y-3 overflow-hidden flex flex-col">
						<div className="flex items-center gap-2 pb-2">
							<FileText className="w-5 h-5 text-muted-foreground" />
							<h3 className="text-lg font-semibold">知识库详情</h3>
							{selectedResult && (
								<Badge variant="outline">ID: {selectedResult.knowledge_detail.knowledge_id}</Badge>
							)}
						</div>

						<ScrollArea className="flex-1 pr-4">
							{selectedResult ? (
								<Card>
									<CardHeader>
										<CardTitle className="text-base">
											知识详情内容
											{selectedResult.knowledge_detail.version && (
												<Badge variant="outline" className="ml-2">
													版本 {selectedResult.knowledge_detail.version}
												</Badge>
											)}
										</CardTitle>
									</CardHeader>
									<CardContent className="space-y-4">
										{/* 知识详情内容 */}
										{selectedResult.knowledge_detail.content ? (
											<div className="prose prose-sm max-w-none">
												<pre className="whitespace-pre-wrap text-sm">
													{selectedResult.knowledge_detail.content}
												</pre>
											</div>
										) : (
											<p className="text-sm text-muted-foreground italic">
												暂无知识详情内容
											</p>
										)}

										<Separator />

										{/* 参考资料 */}
										{selectedResult.knowledge_detail.reference && (
											<div>
												<h4 className="text-sm font-medium mb-2">参考资料</h4>
												<a
													href={selectedResult.knowledge_detail.reference}
													target="_blank"
													rel="noopener noreferrer"
													className="text-sm text-blue-600 hover:underline break-all"
												>
													{selectedResult.knowledge_detail.reference}
												</a>
											</div>
										)}
									</CardContent>
								</Card>
							) : (
								<div className="flex items-center justify-center h-full text-muted-foreground">
									<div className="text-center">
										<FileText className="w-12 h-12 mx-auto mb-2 opacity-50" />
										<p className="text-sm">请选择左侧记录查看详情</p>
									</div>
								</div>
							)}
						</ScrollArea>
					</div>
				</div>
			)}

			{/* 无数据状态 */}
			{!loading && searchResults.length === 0 && !error && (
				<div className="text-center py-12 text-muted-foreground">
					<Search className="w-12 h-12 mx-auto mb-4 text-gray-300" />
					<p className="text-lg mb-2">开始搜索数据表格</p>
					<p className="text-sm">输入关键词来搜索表格记录和知识库详情</p>
				</div>
			)}
		</div>
	);
}
