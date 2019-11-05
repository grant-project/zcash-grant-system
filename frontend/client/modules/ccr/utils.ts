import { CCRDraft, User } from 'types';
import { getAmountError } from 'utils/validators';
// import { PROPOSAL_CATEGORY, PROPOSAL_STAGE } from 'api/constants';
// import {
//   ProposalDetail,
//   PROPOSAL_DETAIL_INITIAL_STATE,
// } from 'modules/proposals/reducers';

interface CCRFormErrors {
  title?: string;
  brief?: string;
  target?: string;
  content?: string;
}

export type KeyOfForm = keyof CCRFormErrors;
export const FIELD_NAME_MAP: { [key in KeyOfForm]: string } = {
  title: 'Title',
  brief: 'Brief',
  target: 'Target amount',
  content: 'Details',
};

const requiredFields = ['title', 'brief', 'category', 'target', 'content'];

export function getCCRErrors(
  form: Partial<CCRDraft>,
  skipRequired?: boolean,
): CCRFormErrors {
  const errors: CCRFormErrors = {};
  const { title, content, brief, target } = form;

  // Required fields with no extra validation
  if (!skipRequired) {
    for (const key of requiredFields) {
      if (!form[key as KeyOfForm]) {
        errors[key as KeyOfForm] = `${FIELD_NAME_MAP[key as KeyOfForm]} is required`;
      }
    }
  }

  // Title
  if (title && title.length > 60) {
    errors.title = 'Title can only be 60 characters maximum';
  }

  // Brief
  if (brief && brief.length > 140) {
    errors.brief = 'Brief can only be 140 characters maximum';
  }

  // Content limit for our database's sake
  if (content && content.length > 250000) {
    errors.content = 'Details can only be 250,000 characters maximum';
  }

  // Amount to raise
  const targetFloat = target ? parseFloat(target) : 0;
  if (target && !Number.isNaN(targetFloat)) {
    const limit = parseFloat(process.env.PROPOSAL_TARGET_MAX as string);
    const targetErr = getAmountError(targetFloat, limit, 0.001);
    if (targetErr) {
      errors.target = targetErr;
    }
  }

  return errors;
}

export function validateUserProfile(user: User) {
  if (user.displayName.length > 50) {
    return 'Display name can only be 50 characters maximum';
  } else if (user.title.length > 50) {
    return 'Title can only be 50 characters maximum';
  }

  return '';
}

// This is kind of a disgusting function, sorry.
// export function makeProposalPreviewFromDraft(draft: CCRDraft): ProposalDetail {
//   const { invites, ...rest } = draft;
//   const target = parseFloat(draft.target);
//
//   return {
//     ...rest,
//     ccrId: 0,
//     status: CCRSTATUS.DRAFT,
//     proposalUrlId: '0-title',
//     proposalAddress: '0x0',
//     payoutAddress: '0x0',
//     dateCreated: Date.now() / 1000,
//     datePublished: Date.now() / 1000,
//     dateApproved: Date.now() / 1000,
//     target: toZat(draft.target),
//     funded: Zat('0'),
//     contributionMatching: 0,
//     contributionBounty: Zat('0'),
//     percentFunded: 0,
//     stage: PROPOSAL_STAGE.PREVIEW,
//     category: draft.category || PROPOSAL_CATEGORY.CORE_DEV,
//     isStaked: true,
//     arbiter: {
//       status: PROPOSAL_ARBITER_STATUS.ACCEPTED,
//     },
//     acceptedWithFunding: false,
//     authedFollows: false,
//     followersCount: 0,
//     authedLiked: false,
//     likesCount: 0,
//     ...PROPOSAL_DETAIL_INITIAL_STATE,
//   };
// }
