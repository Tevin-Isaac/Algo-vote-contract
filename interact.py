import time
from vote import Voting
from beaker import sandbox
from beaker.client import ApplicationClient
from beaker.client.api_providers import AlgoNode, Network
from algosdk.atomic_transaction_composer import TransactionWithSigner
from algosdk.transaction import AssetTransferTxn



client = AlgoNode(Network.TestNet).algod()

accts = sandbox.get_accounts()

creator_account = accts.pop()
acct1 = accts.pop()
acct2 = accts.pop()

app = Voting()

app_client = ApplicationClient(client=client, app=app, signer=creator_account.signer)


def test_app():
    sp = client.suggested_params()

    app_id, app_addr, txid = app_client.create()
    print(
        f"App created with app id: {app_id} and app addr: {app_addr} and signed with: {txid}\n"
    )

    app_client.fund(amt=1_000_000, addr=app_addr)
    app_client.fund(amt=1_000_000, addr=acct1.address)
    app_client.fund(amt=1_000_000, addr=acct2.address)

    app_client.call(app.create_asset, asset_name="Energy New Bal", unit_name="ENB", total_supply=1_000_000, decimals=0)

    asset_id = app_client.call(app.get_token_id).return_value
    print(f"Asset ID: {asset_id}\n")

    # Acct 1
    acct1_app_client = app_client.prepare(signer=acct1.signer)
    txn1 = TransactionWithSigner(
        txn=AssetTransferTxn(
            sender=acct1.address, sp=sp, receiver=acct1.address, amt=0, index=asset_id
        ),
        signer=acct1.signer,
    )
    acct1_app_client.call(app.optin_asset, txn=txn1)
    app_client.call(app.transfer_asset, receiver=acct1.address, amount=1_000)


    acct2_app_client = app_client.prepare(signer=acct2.signer)
    txn2 = TransactionWithSigner(
        txn=AssetTransferTxn(
            sender=acct2.address, sp=sp, receiver=acct2.address, amt=0, index=asset_id
        ),
        signer=acct2.signer,
    )
    acct2_app_client.call(app.optin_asset, txn=txn2)
    print(
        f"Total ENB holdings of account 2 before transfer: {app_client.call(app.get_asset_bal, account=acct2.address).return_value:,}\n"
    )
    app_client.call(app.transfer_asset, receiver=acct2.address, amount=2000)

    time_diff = 30 # 30 seconds

    app_client.call(
        app.create_registration_and_voting,
        reg_begin=0,
        reg_end=time_diff,
        vote_begin=time_diff + 2,
        vote_end=time_diff + 360,
    )

    acct1_app_client.opt_in()
    print("Account 1 registered successfully")
    acct2_app_client.opt_in()
    print("Account 2 registered successfully\n")

    print(f"Account 1 state: {acct1_app_client.get_account_state()}")
    print(f"Account 2 state: {acct2_app_client.get_account_state()}")
    print(f"App state: {app_client.get_application_state()}\n")

    print("Waiting for voting period")
    time.sleep(time_diff + 2)
    print("Voting period begins\n")

    acct1_app_client.call(app.cast_vote, choice="yes")
    acct2_app_client.call(app.cast_vote, choice="yes")

    print(
        f"Account 1 vote choice: {acct1_app_client.get_account_state()['vote_choice']}"
    )
    print(
        f"Account 2 vote choice: {acct2_app_client.get_account_state()['vote_choice']}\n"
    )

    print(
        f"Account 1 vote amount: {acct1_app_client.get_account_state()['vote_amount']}"
    )
    print(
        f"Account 2 vote amount: {acct2_app_client.get_account_state()['vote_amount']}\n"
    )

    print(f"Total vote count: {app_client.get_application_state()['vote_count']}\n")

    acct1_app_client.close_out()


test_app()


