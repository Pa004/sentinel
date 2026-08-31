import { fetchUsers } from "../repository/user_repo";

export function App() {
  const users = fetchUsers();
  return users;
}
