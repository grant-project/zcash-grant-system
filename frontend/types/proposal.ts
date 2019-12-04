import { Zat, Usd } from 'utils/units';
import { PROPOSAL_STAGE } from 'api/constants';
import { CreateMilestone, Update, User, Comment, ContributionWithUser } from 'types';
import { ProposalMilestone } from './milestone';
import { RFP } from './rfp';

export interface TeamInvite {
  id: number;
  dateCreated: number;
  address: string;
  accepted: boolean | null;
}

export interface Contributor {
  address: string;
  contributionAmount: Zat;
  refundVote: boolean;
  refunded: boolean;
  proportionalContribution: string;
  milestoneNoVotes: boolean[];
}

export interface ProposalArbiter {
  user?: User; // only set if there is nomination/acceptance
  proposal: Proposal;
  status: PROPOSAL_ARBITER_STATUS;
}

export type ProposalProposalArbiter = Omit<ProposalArbiter, 'proposal'>;
export type UserProposalArbiter = Omit<ProposalArbiter, 'user'>;

export interface ProposalDraft {
  proposalId: number;
  dateCreated: number;
  title: string;
  brief: string;
  content: string;
  stage: PROPOSAL_STAGE;
  target: string;
  payoutAddress: string;
  milestones: CreateMilestone[];
  team: User[];
  invites: TeamInvite[];
  status: STATUS;
  isStaked: boolean;
  tipJarAddress: string | null;
  deadlineDuration?: number;
  rfp?: RFP;
  rfpOptIn?: boolean;
}

export interface Proposal extends Omit<ProposalDraft, 'target' | 'invites'> {
  proposalAddress: string;
  proposalUrlId: string;
  target: Zat | Usd;
  funded: Zat | Usd;
  percentFunded: number;
  contributionMatching: number;
  contributionBounty: Zat;
  milestones: ProposalMilestone[];
  currentMilestone?: ProposalMilestone;
  datePublished: number | null;
  dateApproved: number | null;
  arbiter: ProposalProposalArbiter;
  acceptedWithFunding: boolean | null;
  isVersionTwo: boolean;
  authedFollows: boolean;
  followersCount: number;
  authedLiked: boolean;
  likesCount: number;
  tipJarViewKey: string | null;
  isTeamMember?: boolean; // FE derived
  isArbiter?: boolean; // FE derived
}

export interface TeamInviteWithProposal extends TeamInvite {
  proposal: Proposal;
}

export interface ProposalComments {
  proposalId: Proposal['proposalId'];
  totalComments: number;
  comments: Comment[];
}

export interface ProposalUpdates {
  proposalId: Proposal['proposalId'];
  updates: Update[];
}

export interface ProposalContributions {
  proposalId: Proposal['proposalId'];
  top: ContributionWithUser[];
  latest: ContributionWithUser[];
}

export interface UserProposal {
  proposalId: number;
  status: STATUS;
  title: string;
  brief: string;
  funded: Zat | Usd;
  target: Zat | Usd;
  dateCreated: number;
  dateApproved: number;
  datePublished: number;
  team: User[];
  rejectReason: string;
  acceptedWithFunding: boolean | null;
  isVersionTwo: boolean;
}

// NOTE: sync with backend/grant/proposal/models.py STATUSES
export enum STATUS {
  DRAFT = 'DRAFT',
  STAKING = 'STAKING',
  PENDING = 'PENDING',
  APPROVED = 'APPROVED',
  REJECTED = 'REJECTED',
  LIVE = 'LIVE',
  DELETED = 'DELETED',
}

export enum PROPOSAL_ARBITER_STATUS {
  MISSING = 'MISSING',
  NOMINATED = 'NOMINATED',
  ACCEPTED = 'ACCEPTED',
}
