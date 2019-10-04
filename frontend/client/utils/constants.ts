export const DONATION = {
  ZCASH_TRANSPARENT: 't1aib2cbwPVrFfrjGGkhWD67imdBet1xDTr',
  ZCASH_SPROUT:
    'zcWGwZU7FyUgpdrWGkeFqCEnvhLRDAVuf2ZbhW4vzNMTTR6VUgfiBGkiNbkC4e38QaPtS13RKZCriqN9VcyyKNRRQxbgnen',
  ZCASH_SAPLING:
    'zs15el0hzs4w60ggfy6kq4p3zttjrl00mfq7yxfwsjqpz9d7hptdtkltzlcqar994jg2ju3j9k85zk',
};

// cutoff time in milliseconds to display contributions on proposals
// proposals published before this time will show contributions
export const CONTRIBUTIONS_CUTOFF = 1570219128; // TODO: update value before deploying to prod
