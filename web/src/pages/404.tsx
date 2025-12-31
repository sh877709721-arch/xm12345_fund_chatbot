import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 px-4">
      <div className="text-center max-w-md">
        <h1 className="text-9xl font-bold text-indigo-600 mb-4">404</h1>
        <h2 className="text-3xl font-semibold text-gray-800 mb-6">
          页面未找到
        </h2>
        <p className="text-gray-600 mb-8 text-lg">
          抱歉，您查找的页面不存在或已被移动。
        </p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link
            to="/"
            className="px-6 py-3 bg-indigo-600 text-white font-medium rounded-md hover:bg-indigo-700 transition-colors shadow-md">
            返回主页
          </Link>
          <Link
            to="/admin"
            className="px-6 py-3 bg-white text-indigo-600 font-medium rounded-md hover:bg-gray-100 transition-colors shadow-md border border-indigo-200">
            返回控制台
          </Link>
        </div>
      </div>
    </div>
  );
}
