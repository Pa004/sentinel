import { db } from '../domain/db';

export function fetchData() {
  return db.query();
}
