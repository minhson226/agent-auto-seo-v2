/**
 * Keywords hook
 */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import * as keywordsAPI from '../api/keywords';

export function useKeywords(workspace_id?: string, page: number = 1) {
  const queryClient = useQueryClient();

  const keywordLists = useQuery({
    queryKey: ['keyword-lists', workspace_id, page],
    queryFn: () => keywordsAPI.getKeywordLists(workspace_id!, page),
    enabled: !!workspace_id,
  });

  const uploadKeywords = useMutation({
    mutationFn: keywordsAPI.uploadKeywords,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['keyword-lists'] });
    },
  });

  const deleteKeywordList = useMutation({
    mutationFn: keywordsAPI.deleteKeywordList,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['keyword-lists'] });
    },
  });

  return {
    keywordLists,
    uploadKeywords,
    deleteKeywordList,
  };
}

export function useKeywordListStats(list_id?: string) {
  return useQuery({
    queryKey: ['keyword-list-stats', list_id],
    queryFn: () => keywordsAPI.getKeywordListStats(list_id!),
    enabled: !!list_id,
  });
}
