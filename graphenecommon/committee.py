from .blockchainobject import BlockchainObject
from .exceptions import CommitteeMemberDoesNotExistsException


class Committee(BlockchainObject):
    """ Read data about a Committee Member in the chain

        :param str member: Name of the Committee Member
        :param bitshares blockchain_instance: BitShares() instance to use when
            accesing a RPC
        :param bool lazy: Use lazy loading

    """

    type_id = None
    account_class = None

    def __init__(self, *args, **kwargs):
        assert self.type_id
        assert self.account_class
        BlockchainObject.__init__(self, *args, **kwargs)

    def refresh(self):
        if self.test_valid_objectid(self.identifier):
            _, i, _ = self.identifier.split(".")
            if int(i) == 2:
                account = self.account_class(self.identifier, blockchain_instance=self.blockchain)
                member = self.blockchain.rpc.get_committee_member_by_self.account_class(
                    account["id"]
                )
            elif int(i) == 5:
                member = self.blockchain.rpc.get_object(self.identifier)
            else:
                raise CommitteeMemberDoesNotExistsException
        else:
            # maybe identifier is an account name
            account = self.account_class(self.identifier, blockchain_instance=self.blockchain)
            member = self.blockchain.rpc.get_committee_member_by_self.account_class(account["id"])

        if not member:
            raise CommitteeMemberDoesNotExistsException
        super(Committee, self).__init__(member, blockchain_instance=self.blockchain)
        self.account_id = member["committee_member_account"]

    @property
    def account(self):
        return self.account_class(self.account_id, blockchain_instance=self.blockchain)
