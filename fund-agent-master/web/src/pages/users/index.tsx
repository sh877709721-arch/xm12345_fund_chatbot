import { Link } from "react-router-dom";

export default function Users() {
  return (
    <div>
      <h1>Users Page</h1>
      <ul>
        <li><Link to="/users/1">User 1</Link></li>
        <li><Link to="/users/2">User 2</Link></li>
        <li><Link to="/users/3">User 3</Link></li>
      </ul>
      <Link to="/">Go back to Home</Link>
    </div>
  );
}