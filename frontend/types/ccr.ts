import { User } from 'types/user';

export enum CCRSTATUS {
  DRAFT = 'DRAFT',
  STAKING = 'STAKING',
  PENDING = 'PENDING',
  APPROVED = 'APPROVED',
  REJECTED = 'REJECTED',
  LIVE = 'LIVE',
  DELETED = 'DELETED',
}

export interface CCRDraft {
  author: User;
  title: string;
  brief: string;
  ccrId: number;
  status: CCRSTATUS;
  target: string;
  dateCreated: number;
  content: string;
  isStaked: boolean;
}

export interface CCR extends CCRDraft {
  // TODO remove
  noOp: boolean;
}

export interface UserCCR {
  ccrId: number;
  status: CCRSTATUS;
  title: string;
  brief: string;
  dateCreated: number;
  dateApproved: number;
  datePublished: number;
  rejectReason: string;
}
