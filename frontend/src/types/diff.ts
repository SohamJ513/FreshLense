export enum ChangeType {
  ADDED = "added",
  REMOVED = "removed",
  MODIFIED = "modified"
}

export interface ContentChange {
  change_type: ChangeType;
  old_content: string;
  new_content: string;
  line_range_old: [number, number];
  line_range_new: [number, number];
}

export interface DiffRequest {
  old_version_id: string;
  new_version_id: string;
}

export interface DiffResponse {
  page_id: string;
  old_version_id: string;
  new_version_id: string;
  old_timestamp: string;
  new_timestamp: string;
  changes: ContentChange[];
  total_changes: number;
}