import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export default function DashboardMain() {
  // 模拟待办事项数据
  const todos = [
    { id: 1, title: "项目搭建", status: "completed" },
    { id: 2, title: "知识库管理", status: "completed" },
    { id: 3, title: "知识测试", status: "completed" },
    { id: 4, title: "机器人", status: "in-progress" },
    { id: 5, title: "用户管理", status: "completed" },
    { id: 6, title: "设置页面", status: "completed" },
  ];

  // 分类任务
  const completedTasks = todos.filter((todo) => todo.status === "completed");
  const inProgressTasks = todos.filter((todo) => todo.status === "in-progress");
  const pendingTasks = todos.filter((todo) => todo.status === "pending");

  // 计算完成进度
  const completedCount = completedTasks.length;
  const totalCount = todos.length;
  const progressPercentage =
    totalCount > 0 ? (completedCount / totalCount) * 100 : 0;

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">智能客服后台功能</h1>

      {/* 进度概览卡片 */}
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>项目进度</CardTitle>
          <CardDescription>
            {completedCount}/{totalCount} 项任务已完成
          </CardDescription>
          <div className="w-full bg-gray-200 rounded-full h-4 mt-2">
            <div
              className="bg-green-600 h-4 rounded-full transition-all duration-500 ease-in-out"
              style={{ width: `${progressPercentage}%` }}></div>
          </div>
        </CardHeader>
      </Card>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* 已完成的任务 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>已完成</span>
              <Badge
                variant="secondary"
                className="bg-green-100 text-green-800">
                {completedTasks.length}
              </Badge>
            </CardTitle>
          </CardHeader>
          <div className="px-6 pb-6">
            {completedTasks.length > 0 ? (
              <ul className="space-y-3">
                {completedTasks.map((todo) => (
                  <li
                    key={todo.id}
                    className="flex items-center justify-between p-3 bg-green-50 rounded-lg border border-green-100">
                    <span className="text-gray-800">{todo.title}</span>
                    <Badge
                      variant="secondary"
                      className="bg-green-500 text-white">
                      完成
                    </Badge>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-500 italic py-2">暂无已完成的任务</p>
            )}
          </div>
        </Card>

        {/* 处理中的任务 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>处理中</span>
              <Badge variant="secondary" className="bg-blue-100 text-blue-800">
                {inProgressTasks.length}
              </Badge>
            </CardTitle>
          </CardHeader>
          <div className="px-6 pb-6">
            {inProgressTasks.length > 0 ? (
              <ul className="space-y-3">
                {inProgressTasks.map((todo) => (
                  <li
                    key={todo.id}
                    className="flex items-center justify-between p-3 bg-blue-50 rounded-lg border border-blue-100">
                    <span className="text-gray-800">{todo.title}</span>
                    <Badge
                      variant="secondary"
                      className="bg-blue-500 text-white">
                      进行中
                    </Badge>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-500 italic py-2">暂无处理中的任务</p>
            )}
          </div>
        </Card>

        {/* 待办的任务 */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>待办</span>
              <Badge
                variant="secondary"
                className="bg-yellow-100 text-yellow-800">
                {pendingTasks.length}
              </Badge>
            </CardTitle>
          </CardHeader>
          <div className="px-6 pb-6">
            {pendingTasks.length > 0 ? (
              <ul className="space-y-3">
                {pendingTasks.map((todo) => (
                  <li
                    key={todo.id}
                    className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg border border-yellow-100">
                    <span className="text-gray-800">{todo.title}</span>
                    <Badge
                      variant="secondary"
                      className="bg-yellow-500 text-white">
                      待办
                    </Badge>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-500 italic py-2">暂无待办的任务</p>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
}
