"""P243 finite source-authenticated Git transport candidate. Production HOLD."""
from __future__ import annotations

# Each row is an exact commit:path, Git blob OID, and ORIGINAL literal pin.
# The associated source/rule is fixed by SPECS below. No refs learn trust.
ROWS = (
    # phase_8_30_scope_migration -- 5 entries
    ("6030f9b7afacd0543912bfb4a8b4fe610ebd9632:nayeon/desktop_alpha/application.py", "3b311acdb12ac8208e6241b01c266b6a4371d5f2", "289251bd72b35d9a0e9c840bca5e0d7eb6c4328bd28a8e9149de80076f2e6b05"),
    ("6030f9b7afacd0543912bfb4a8b4fe610ebd9632:nayeon/desktop_alpha/presentation_profile_owner.py", "640e60b27afee8a34922354aa4694e04a7a6f952", "c17ec6eca4637b9a28dbe51e6a3cd3481c8a631dae23c30353c39777f5c1bd38"),
    ("6030f9b7afacd0543912bfb4a8b4fe610ebd9632:nayeon/desktop_alpha/presentation_window.py", "0a81e2b3d275dd7f6ad0063bea27a96cd479b0c6", "d78ce629162ffaca652a8c7681cf3e637e49547b5c86f9a5b2ec9a98dede79ce"),
    ("6030f9b7afacd0543912bfb4a8b4fe610ebd9632:nayeon/desktop_alpha/window.py", "a88ae09472293c54231926bb24c068544a06b4f2", "9a448db3fc793d7af7aad2cb56d10c79af90ab4cd50c2f762b230b1f1d396e92"),
    ("6030f9b7afacd0543912bfb4a8b4fe610ebd9632:nayeon/desktop_alpha/workspace_window.py", "d42371e231f196ed3d11565eabdc89830fdd3b02", "2730f8f610f5bb272571f06a8eb523aa7e8c4a95d1518e7365177bfe695c46d8"),
    # phase_8_31_scope_migration -- 3 entries
    ("79f17ca5211d7e1a97ef99b83dd613885d693bef:nayeon/desktop_alpha/application.py", "87d4b71f4934c66e36ae215ce022fedd0ee00374", "d520d14f98a7e96480c8f975c93ba43026b77eb72655dfdafd78666cf72d8c71"),
    ("79f17ca5211d7e1a97ef99b83dd613885d693bef:nayeon/desktop_alpha/conversation_session.py", "3081be0955c00b33dc2430403951d5a311504851", "cddffbba99b557381a415f2a13c861069c41b8694dfbdcdf0b77a0ab552ffa92"),
    ("79f17ca5211d7e1a97ef99b83dd613885d693bef:nayeon/desktop_alpha/workspace_window.py", "b21ebb4df66b04c12ce5c53c06bb2e799cdaa079", "93ee3396291cdd80a57754fbf3bd8382233d6ebd166102ead6004cb5af712376"),
    # phase_8_32_scope_migration -- 14 entries
    ("03f247d8627bf1c51105f73b9de5c6bbdf389cf9:.codex/CURRENT_STATE.md", "320c68f17e5ed6fca2fbac03acdd941f6dc2de61", "6f1432c27a13e0c37bba707881d766899148a9e14a937b95317f8b3ac164c58f"),
    ("03f247d8627bf1c51105f73b9de5c6bbdf389cf9:docs/phase_8_32_lifecycle_assurance_review.md", "ae7e83012125e1ee0a9998e739be9fe779f8be0a", "f9dea6c87a790c748a0283aff25e4f84051de23f99ec0c9ca7bbbd181ca8656c"),
    ("03f247d8627bf1c51105f73b9de5c6bbdf389cf9:docs/phase_8_32_reply_admission_rfc.md", "aa05e5847e7e487295b0ffcf33475fb1fb794d5a", "8d464121d27914d0f7d52b24578767d05ad0c72625b93cbdfd0a90c34f0c152d"),
    ("03f247d8627bf1c51105f73b9de5c6bbdf389cf9:docs/pre_829_shutdown_ownership_failure_ledger.md", "c6649ad72ee65c5e3300fe1167c6e38d78b4ccbe", "4827b5be8bfd2d5a125cc680a4964f1ce65c0f0e2862c2c7dc9c21b3e973a872"),
    ("03f247d8627bf1c51105f73b9de5c6bbdf389cf9:nayeon/desktop_alpha/application.py", "1b4a2e5be36bdce117062c3d95c9558b81b50613", "389e67caf1851cb95d6b3cca7b120d21d6724d9d514e952445311eb7ecee97be"),
    ("03f247d8627bf1c51105f73b9de5c6bbdf389cf9:nayeon/desktop_alpha/presentation_window.py", "964656e746a8245ef3483e16045e92dd37d4a3cf", "fd19160fc76a8334b9447c0ef3307cb8211c71efa679eafaf31d3289208ab9b0"),
    ("03f247d8627bf1c51105f73b9de5c6bbdf389cf9:nayeon/desktop_alpha/workspace_window.py", "9158706041521225825ac815a13c3263a528d017", "85a2227e07921b88bacc6719ff62aa6107b83a0e0882ccc89e2cdb9d35cda1a0"),
    ("03f247d8627bf1c51105f73b9de5c6bbdf389cf9:tests/phase_8_31_scope_migration.py", "11734159f8be579b1b943383e7c838341ed8a976", "f1a0772533803b69719ad5af1d8ad1f84946b194259e682cbf809bcff83a5c99"),
    ("03f247d8627bf1c51105f73b9de5c6bbdf389cf9:tests/phase_8_32_scope_migration.py", "3ff91c2141e36c5259f95f9524287958eaa131e2", "e79b338eeb7d79e73b887c94a2245e1f11d2d7cdfb04e7b0bdadb6d81249598f"),
    ("03f247d8627bf1c51105f73b9de5c6bbdf389cf9:tests/test_phase_830_scope_integrity.py", "4e3c069154c1a0b6709a098c475b953cabe06972", "760ef3f881f3acc214a0419e5691cb17552e745d3fbc9f3f98245c7e7eadf532"),
    ("03f247d8627bf1c51105f73b9de5c6bbdf389cf9:tests/test_phase_831_scope_integrity.py", "9206d6183274a6e479543a058a91862332901675", "082dcd64ecf11ae3507be3db0c63a69d32ee92f41196f25c9b99f3aa7bb73a5c"),
    ("03f247d8627bf1c51105f73b9de5c6bbdf389cf9:tests/test_phase_831_workspace.py", "72af93416498084c14eafe03b00d8ba93541e55b", "33a5a624b3242ef95f0a52572cb2fe4c224bcd9a048bb94b1b7a29b4f45c1125"),
    ("03f247d8627bf1c51105f73b9de5c6bbdf389cf9:tests/test_phase_832_lifecycle_assurance.py", "35e19ecc3ca36193c7481f3beea7858da7ba19bd", "99b7ab4c9cbcb22d44ab4ddd734345e681b54fa317b1f0e1951683b10830dd54"),
    ("03f247d8627bf1c51105f73b9de5c6bbdf389cf9:tests/test_phase_832_scope_integrity.py", "70682a06d6f2f7a5bda971b4cf592056cd62a1e4", "e185b0a144293cd37072a6b299e56feb13de5ea3409930e985b900437bfc46b3"),
    # phase_8_33_scope_migration -- 16 entries
    ("1a972d1d292597239c938d53437218c536b5bf3f:.codex/CURRENT_STATE.md", "ba86f7a96cd6841cc364834f39c0ad39a49046d2", "32a534729a0d536c506a6e76ebbdbe11c3c7bb337b7b5b936dfbfed98e8f747d"),
    ("1a972d1d292597239c938d53437218c536b5bf3f:docs/phase_8_33_offline_delayed_completion_review.md", "77683856add7a4537818def94f16603110db0f00", "061d0f82716ac39a00c5408798e0aed82b8c56a1dc42fa5ffc3b1da4e9617ea4"),
    ("1a972d1d292597239c938d53437218c536b5bf3f:docs/phase_8_33_offline_delayed_completion_rfc.md", "81ee2f73ad5a2c21798da538dd861bade597d44b", "a9280400e87594e3cb634c1ed5dacf7e07cd9ed205db29899f529934a6be2191"),
    ("1a972d1d292597239c938d53437218c536b5bf3f:docs/pre_829_shutdown_ownership_failure_ledger.md", "cf9372ee3b9cd4139d2675619f1adf6968482264", "295b5fcddc4e66870fa031464f6d169d4291b85952db167844fa4850fb44c7f8"),
    ("1a972d1d292597239c938d53437218c536b5bf3f:nayeon/desktop_alpha/application.py", "60a08eba6306054bb54ee4286a7db16afc22dbe3", "f68ca2cbdb00da8722a040d9877829ec3eae98a0c72fc3f86e034703e00d0a26"),
    ("1a972d1d292597239c938d53437218c536b5bf3f:nayeon/desktop_alpha/offline_completion_admission.py", "752370d7ce0baa9ef262a8d88441c3152a9da853", "e2471a0dbc226959a609d21e90c26891cab81a172323b2afada364fe856c7bf4"),
    ("1a972d1d292597239c938d53437218c536b5bf3f:nayeon/desktop_alpha/workspace_window.py", "58a4f42e863f12ebcd0effeb07133229338d76dd", "240423f7423b77ffc80ea22568af93963b0d2cf09b6938a5917f19b5682d72c4"),
    ("1a972d1d292597239c938d53437218c536b5bf3f:tests/phase_8_30_scope_migration.py", "999c780877da0d3419f287b11fe9b644bbebcc37", "8661cc9f5901c7f25a71f8ef64f273dcda718b108f44f78f91037c533861780d"),
    ("1a972d1d292597239c938d53437218c536b5bf3f:tests/phase_8_32_scope_migration.py", "fd6b1c5599d3fd112bec0c518cec2a6ead3f4412", "d658f8442c97225ac9ed1ddef187e25a6d423e6b2eeda3fcd6771fe47e11be02"),
    ("1a972d1d292597239c938d53437218c536b5bf3f:tests/phase_8_33_scope_migration.py", "2bfa3f75651c5450d13e17be7c1ab4562ee4ad1b", "f0766e2c6dc91f007ea3d9dea22a1ef22e8f2d1a46d8282f90e6b419b5c69a01"),
    ("1a972d1d292597239c938d53437218c536b5bf3f:tests/test_phase_830_scope_integrity.py", "2c6f95cc5587e7725e938535ef40be0ed3de5bc1", "173c9fbce0d7844cdf50ee3c76580df71904960f43c68205dc98bf8ce103ed89"),
    ("1a972d1d292597239c938d53437218c536b5bf3f:tests/test_phase_831_scope_integrity.py", "f49121f4172652958796cd230f11d85584c79eed", "7b91541715158410673eb63ade7987ad0a56a41cb60d2d695c23cfa0bc6f8846"),
    ("1a972d1d292597239c938d53437218c536b5bf3f:tests/test_phase_832_scope_integrity.py", "56736dd4136bad7f5bd51b21afb62a757890a3d5", "1892597e8469aa715ef73ff267bebb6edc99be091a4735abd04f44742ab355dc"),
    ("1a972d1d292597239c938d53437218c536b5bf3f:tests/test_phase_833_offline_completion.py", "67e894d11fc61e8310e121515a86c32bb59203ee", "9e4a0ae706de22f85307714801f0bbcd63f343571dbc37fd83d5bfdf45b0897f"),
    ("1a972d1d292597239c938d53437218c536b5bf3f:tests/test_phase_833_scope_integrity.py", "8559cf78c0222f920c2c487edab43d61089fc979", "d2cdef4307fb1bce62f50855282b47f4e85348b2f1efb9f15cf1ff9cff1b216f"),
    ("1a972d1d292597239c938d53437218c536b5bf3f:tests/test_phase_833_tk_completion.py", "8e471b024d4848f2afa35cac089708d133fbaa73", "4144e3efa6a753e27b3f5a2fb0713b72d401ee947254068e721109017a443f2f"),
    # phase_8_34_scope_migration -- 20 entries
    ("b0490cd9e72104a74a32dc5315cbc55bc4034676:.codex/CURRENT_STATE.md", "fdefc16a0232475ecbce97856ddf4661511d2b5f", "b8bf243847c6958626c218490ebbe4a33220cdc019a3f6ddeeeef117d8ec6a55"),
    ("b0490cd9e72104a74a32dc5315cbc55bc4034676:docs/phase_8_34_text_reply_review.md", "e5de02d264bd8b408c5673d9c3ae1a5a85fba02d", "fdf290bc3b87e63e1f02bf99affb76b5ab7ef11547e3c9e11fc455751032a0f6"),
    ("b0490cd9e72104a74a32dc5315cbc55bc4034676:docs/phase_8_34_text_reply_rfc.md", "eb31bd83eec134693802cf5a801fde0aec00c1ad", "41f156cba8518feffc76ccaa4bfbd54f46452e461f687359eef65c47a1d0c9ab"),
    ("b0490cd9e72104a74a32dc5315cbc55bc4034676:docs/pre_829_shutdown_ownership_failure_ledger.md", "00467d9f401419f25f703e362ed32761b8377140", "5963c9b9e5b9af67ced957de1da6e2e8c4558da72141eaae4bde6b181ff07e2b"),
    ("b0490cd9e72104a74a32dc5315cbc55bc4034676:nayeon/desktop_alpha/application.py", "00daae05fcf93e17017b7a949719dd362b98fad8", "035f5c8d6ea131b1dd4bb3aa061ff96662d1b926c4321e9a1bfe2eef700181e7"),
    ("b0490cd9e72104a74a32dc5315cbc55bc4034676:nayeon/desktop_alpha/reply_contracts.py", "422a3d0031c88b93ea2e149140e2d23478cb84e8", "43499034bbd6f49892b46bb5ff6209a7ceea85cb4392013ce0c2f718a6f208a4"),
    ("b0490cd9e72104a74a32dc5315cbc55bc4034676:nayeon/desktop_alpha/reply_owner.py", "526bb2a867c3fd1c20c67527a3dafa017b223c22", "ed3910a2499a0a8f8bf0e56ea26fe5fbdbb9bfeea2a256f57adf1302d4580dbc"),
    ("b0490cd9e72104a74a32dc5315cbc55bc4034676:nayeon/desktop_alpha/reply_worker.py", "a74a1d0998479c6f1225dc5ba216ea6a03b6a1a3", "68c39289b3920e105912f3ee5e063b584692458d48274f5dade18f782c6b8059"),
    ("b0490cd9e72104a74a32dc5315cbc55bc4034676:nayeon/desktop_alpha/workspace_window.py", "40baf4b617421417269a4f2f12609f7ed6ad1a00", "6d216a4c8ee5e4fae1afca6a10a9298702562f2bec8ad2bb91bd9bebcd4f29b0"),
    ("b0490cd9e72104a74a32dc5315cbc55bc4034676:tests/phase_8_30_scope_migration.py", "3510edad019585c6d96928ea6692be28582e4e1c", "9d82107ff78f8d3765b0f746e5cc7208ec38e05fba55590e54cdbc3a8d42ff78"),
    ("b0490cd9e72104a74a32dc5315cbc55bc4034676:tests/phase_8_33_scope_migration.py", "b708b022f5baf2c767aa5b576ea331adedfa292d", "9af98a6fd435fea19f30ce00d03fb4f47a23ca64e9278fd9b4e06daaf53872bd"),
    ("b0490cd9e72104a74a32dc5315cbc55bc4034676:tests/phase_8_34_scope_migration.py", "0982518bd112b59b45d0a9b85fcd975ea23d1482", "1cb447df709925f41605c5816b3fa03178625120ba7999b6d70335c0f541f176"),
    ("b0490cd9e72104a74a32dc5315cbc55bc4034676:tests/test_phase_830_scope_integrity.py", "116a8efd76eedd127cf73bc8b941edbef405eda5", "2c51136d2c0d4db40dac933114a26e4eaca97dcc76cc7d7a0ff667fae7444cdc"),
    ("b0490cd9e72104a74a32dc5315cbc55bc4034676:tests/test_phase_831_scope_integrity.py", "c6ffb5c907d17ab0c7a43dde091453c50696e947", "d2f930f8bd090b52a6e38295d6e2539e8b287d5bd40cec9db7f68dd655450c86"),
    ("b0490cd9e72104a74a32dc5315cbc55bc4034676:tests/test_phase_832_scope_integrity.py", "cf9853f0e022b8a6e80260dda740d4577e420e12", "4d545739340644c76afff001f369e3740a4c1f623f259564f91482fd72f15cda"),
    ("b0490cd9e72104a74a32dc5315cbc55bc4034676:tests/test_phase_833_scope_integrity.py", "076560da01131d5bc5a7f21a08923e0ac23fb233", "d0e3a4dc7cbc7cd4840cb65f66e2ae3b769bd0cbc258ca0501588d9bd7939542"),
    ("b0490cd9e72104a74a32dc5315cbc55bc4034676:tests/test_phase_834_reply_owner.py", "c9f09944a04b704fd7014949ffc6e61409078722", "f2925b5ea3eda73f542b1574fb20f6538da2fb3c149f482d89c2effa022bd8ee"),
    ("b0490cd9e72104a74a32dc5315cbc55bc4034676:tests/test_phase_834_reply_worker.py", "d809d85422edcf8a9b652282326849ad4295ea31", "152cc95d5b2260069e2364ff983d69b75213dbcec6b43ba0f57fe85739fa9783"),
    ("b0490cd9e72104a74a32dc5315cbc55bc4034676:tests/test_phase_834_scope_integrity.py", "9560cc690f566eafc70e14b5ccd18bdb623abb24", "a18e50f3519c93ebbc1fe40470fcddca79784bda67733f580617aef41c731c53"),
    ("b0490cd9e72104a74a32dc5315cbc55bc4034676:tests/test_phase_834_tk_reply.py", "3a0a01a583dd0150d9078c94a4c160f5e87fe870", "d0971f1e6ff6d5ae6444f10e2da0903e6a1f02b51f8d677f34b0e427394dce94"),
    # phase_8_36_scope_migration -- 19 entries
    ("a12565b9be070684e1d7d801ded4833d13121f94:.codex/CURRENT_STATE.md", "7729fb211150de8c1d3cfd29a6cc615d6172efd5", "4e587a52082129f642eb500d6198a15e210bb5a2f804d28c934af14cda8871b5"),
    ("a12565b9be070684e1d7d801ded4833d13121f94:docs/phase_8_36_offline_request_review_review.md", "02d4d72643b7c0ec5875e5250d59a6ac5458d34f", "95e506a11337731e5654e448f15c5ccf9c9dab912706a3811a2dab70cd440381"),
    ("a12565b9be070684e1d7d801ded4833d13121f94:docs/phase_8_36_offline_request_review_rfc.md", "ee58bd5824f252634c5f42256d3aa3f03a2b30d8", "bc1a589152646126be3ccc94fc0245f90ba5de8fc20fb40dc269cec74b3c62ce"),
    ("a12565b9be070684e1d7d801ded4833d13121f94:docs/pre_829_shutdown_ownership_failure_ledger.md", "7a2539ed9b5a3df565d5791d2e4db82b26c04ab3", "56cb107d533deab58990ff341dce739c748238b926f776dd107fef2d42e4aaeb"),
    ("a12565b9be070684e1d7d801ded4833d13121f94:nayeon/desktop_alpha/application.py", "0914039c817307716a8c8296df2af0d04e419f67", "59c66a2ac3439d2c3d799142bb608221e11d12eb65159c31502bf2d09a1c99f0"),
    ("a12565b9be070684e1d7d801ded4833d13121f94:nayeon/desktop_alpha/offline_request_review.py", "d9cdd4bd9359353dee930c1bfd55c7d9d983a9bf", "5b4fb379d9f907cd14cd2711e651d58445834c01c4ddf067376176ae5fb98884"),
    ("a12565b9be070684e1d7d801ded4833d13121f94:nayeon/desktop_alpha/workspace_window.py", "bcc3aacac7cadab08eafea3a976fa2cda61a4383", "675ad4d338b6a5e7532c85e847e9ee2afaccde4039889cdf70dc6d10081b3a2c"),
    ("a12565b9be070684e1d7d801ded4833d13121f94:tests/phase_8_30_scope_migration.py", "6b58f1f1800a54db46aa740543d23804d505a995", "7aaa31f0c32825fa2ee6cc463c66b6a9a00165bdbb5b1509bf3dae598af2ed48"),
    ("a12565b9be070684e1d7d801ded4833d13121f94:tests/phase_8_34_scope_migration.py", "04295ce3d4c398ccc8be8cdb7bca30a2e33c4899", "59442121254b42949640161fb7dbd47e90f3e77e6045f258a1da130b640c8d43"),
    ("a12565b9be070684e1d7d801ded4833d13121f94:tests/phase_8_36_scope_migration.py", "519a6a146614247c8008b48ebcb30a8de3f257cb", "dc75566dcf6b3df509568f35c14c69b3674cefc285b53daa7e748eecec9a82b9"),
    ("a12565b9be070684e1d7d801ded4833d13121f94:tests/test_phase_830_scope_integrity.py", "d7b3f202e7b945393152d280919da87caedd36db", "fa67d035f9a938a7cdf85208f76a86e3e4a4f13ebef4b909de72d2ac8e8ae506"),
    ("a12565b9be070684e1d7d801ded4833d13121f94:tests/test_phase_831_scope_integrity.py", "9e2def9279baa708b1dbb2fcf115744379bf9249", "f0f09bf7ab27390f2eff0f94f2e07e54eef9ee1ac6341678526f92ddcaf53da9"),
    ("a12565b9be070684e1d7d801ded4833d13121f94:tests/test_phase_832_scope_integrity.py", "1b8a91cf150684423ed265b4b5882b51eb8b2683", "861a1a19dce7e38a38c1c8a02deb4d971e813df4dfbfdd8150e8aa0f3e694e70"),
    ("a12565b9be070684e1d7d801ded4833d13121f94:tests/test_phase_833_scope_integrity.py", "ddaa6ae40f9e891e3ec968908883295ba49a1992", "9b22ed97005807933e36e8fa69e7d1f66c45013888e0f37a5dcb8c034ad70264"),
    ("a12565b9be070684e1d7d801ded4833d13121f94:tests/test_phase_834_scope_integrity.py", "4441a511fb02c91105acdaa7cdaa04fa3aaed592", "ad9c55f8839357cb2bb2e610ac819b282ba75368257302429f88ad0cd9cde4b5"),
    ("a12565b9be070684e1d7d801ded4833d13121f94:tests/test_phase_836_application_review.py", "8b41b6a15df5bdb910eba0e9388a6874424256e5", "f2d71381b3f02f455148c38ce03bf8aa56d8b727391b57af8c26e8ec69f28e4c"),
    ("a12565b9be070684e1d7d801ded4833d13121f94:tests/test_phase_836_offline_request_review.py", "b6412cce0e8a2c6c0de1efc29b8af8d121d989f4", "fe94785b754bcbffa26f66d5201ed9b97154d9b2bf8425634ac842c1ec0367da"),
    ("a12565b9be070684e1d7d801ded4833d13121f94:tests/test_phase_836_scope_integrity.py", "8473775b1308d9e948b5c19be6399bb2027be2d2", "bb2875f277dcebed810a6a48780820b12ef5827ec5e91e89e161a364e28a5acf"),
    ("a12565b9be070684e1d7d801ded4833d13121f94:tests/test_phase_836_tk_request_review.py", "fa0459bad8f9982a598acb2c9bf11d77329ca442", "eb252e3de5717d414dbd495380385dae00f2ad7094cc14ebfef8b4b9b2ed9a2d"),
    # phase_8_37_scope_migration -- 20 entries
    ("87208af710bac90c440f2e0851854318b22e9b88:docs/phase_8_37_provider_request_draft_rfc.md", "abf7926008ca6d68fba7f20edd1671019434edc9", "05f39c622a5772598c48aeaa567dff94339a1e7fdb8634606a0d5d9fefca0301"),
    ("87208af710bac90c440f2e0851854318b22e9b88:nayeon/desktop_alpha/application.py", "0de5875468dda48e4903e67d0818acdec7df3ac2", "4aac135178e4e9f0df9b0f0e46a580d6aff02694dfb1a6677ec65319162cecb0"),
    ("87208af710bac90c440f2e0851854318b22e9b88:nayeon/desktop_alpha/offline_draft_consent.py", "0d96898d5711b2200d2aa9fe050a5c547dc7ccf6", "40d78b7949056dceb337204e8b7ff4e0e6ee18a1e2208de1a00e8b957e4e26e2"),
    ("87208af710bac90c440f2e0851854318b22e9b88:nayeon/desktop_alpha/offline_request_draft.py", "88605fb179cc1e337688d68de418dbea7f881304", "c4d39810d6cb220d3ca9e38e3c9ceab8554ae2b662732ebb24bbc9fe98f24cb3"),
    ("87208af710bac90c440f2e0851854318b22e9b88:nayeon/desktop_alpha/workspace_window.py", "9a8018a572d20e54176048db8369da3ea1d266b2", "dbbaa691cc5caf0f9f1dfc611342a61ecbc5fdc11514c8cd1acfa8cd09c7b63b"),
    ("87208af710bac90c440f2e0851854318b22e9b88:tests/phase_8_30_scope_migration.py", "3e66a768dbea1658d60f589c5de335b12a41c948", "778bf425e0d3ceb69ae9d4a3bf06d627ece1c29bb5f7816722039ed10fd38f40"),
    ("87208af710bac90c440f2e0851854318b22e9b88:tests/phase_8_36_scope_migration.py", "891da824b5e5e3c97db8dc74b4b3aea433913d9f", "d63b58a03a00f573c6474a514f4f4e545b4a5ea3c85478fd824e1276862413e6"),
    ("87208af710bac90c440f2e0851854318b22e9b88:tests/phase_8_37_scope_migration.py", "d9793e44ebaca37bc58d30b2bf6611b703b8b137", "a53ebfd97a7696ca2255918736cd6e6929b1770eaec6318742f509dcb5b99692"),
    ("87208af710bac90c440f2e0851854318b22e9b88:tests/test_phase_830_scope_integrity.py", "fb00b5deccca58adc9f629a2dd509beabbf56c52", "50376cdb904700911bcb78b6a1d5b4298fa9fa3c6b7ea2bb18e2635ab41af454"),
    ("87208af710bac90c440f2e0851854318b22e9b88:tests/test_phase_831_scope_integrity.py", "d9b320f24efffff1f02840bca02364d2958005b1", "70c2c1654d978168c3c58be337cab12e87499d6f2113903ff1c97b957a863f12"),
    ("87208af710bac90c440f2e0851854318b22e9b88:tests/test_phase_832_scope_integrity.py", "641434c02159e3e60439f662dc3ae9ee7e928c1e", "1e4369684ad1b3641367cb8f2a8cce26942a4904bea89b01af79df4c855f9ed0"),
    ("87208af710bac90c440f2e0851854318b22e9b88:tests/test_phase_833_scope_integrity.py", "b48afb51b1d54c3df1551bcd18b1b2dbdf51745b", "0bbd24ac3408a862a91d3cb831b17193e5f01a97422ac1c2f2e8403edb157b37"),
    ("87208af710bac90c440f2e0851854318b22e9b88:tests/test_phase_834_scope_integrity.py", "bcf60ff6eb7f0ba9cbc921c94ed3f412d9b46be8", "c91f4823b705f04bd73b3183734b2368690797ec850cc70416298156627061ef"),
    ("87208af710bac90c440f2e0851854318b22e9b88:tests/test_phase_836_scope_integrity.py", "9e882bad1f46fa75e50a3029344d0bf4e7b873ca", "062980db3522ee9ce5c3d939e50adda426f53fa8c772917ba53d25b142d0dd3d"),
    ("87208af710bac90c440f2e0851854318b22e9b88:tests/test_phase_837_draft_application.py", "682ec7df92dfd76f27f94c3fbd3a9a4aa3eda0ef", "f17301a47a8467d3406659f87f4807816e11d9fc889aa3afb50539c2fb12ee28"),
    ("87208af710bac90c440f2e0851854318b22e9b88:tests/test_phase_837_draft_consent.py", "137e48dbd3e056786953cf2cd4ccbb34bda1230b", "2f976063dea225da1b7c08a232fb7e139d05b032a405d350433fc9a97adeab40"),
    ("87208af710bac90c440f2e0851854318b22e9b88:tests/test_phase_837_draft_tk.py", "c0e83a9dde74f90998dea0e1fa72a023028d0863", "b4a0cb835953edeed884619d94482b8c40757b225bcc88fbb323d65b64f16753"),
    ("87208af710bac90c440f2e0851854318b22e9b88:tests/test_phase_837_offline_request_draft.py", "07ef228951fe0f3ef2de88dd8616a673ce27531e", "86b7d86931e924f9d830faa14c9a34ca738ba14ee881e8f12294b0e48b96b452"),
    ("87208af710bac90c440f2e0851854318b22e9b88:tests/test_phase_837_scope_integrity.py", "231ae4b585917df6cbacabef465945ac563e6419", "129679f8cdf674c156bf871959e8187ecc541f33fb8c5c5ed2863437fb162d08"),
    ("87208af710bac90c440f2e0851854318b22e9b88:tests/test_pre_829_a02_fake_isolation.py", "9a54b2c81c371017e4fa2ab39079c351b9f5a0b7", "ac3c47aa9d37a2afc354f354e50bd6380273a21e095b69f1a6334e2057cd5f69"),
    # phase8_byok_scope_migration -- 11 entries
    ("4110fa69849f8127a325f9a9001284cd1bd3a59c:.codex/CURRENT_STATE.md", "426d7a70a3a77ecb8e60b478d6bdd94d91272972", "9a81ed97ce49c524acd48bc5f3d3ad3fdf73e3b9493d227be61d26690817b8fa"),
    ("4110fa69849f8127a325f9a9001284cd1bd3a59c:docs/phase8_first_run_connection_design.md", "c406b01d7a4057104a8b7891eb7e49c32cdd35e7", "e7f98bf248441db30f7a1d1177432285253d4ed0f8d7d9e690602fc40352fcc3"),
    ("4110fa69849f8127a325f9a9001284cd1bd3a59c:nayeon/desktop_alpha/first_run_connection_owner.py", "da6f3b6d1ff4e207ab17dd77af027656ccbc8d63", "704b968ad65368cde2ae2b6d7c73083c4a68219ba7436c4dee7eccde85493eca"),
    ("4110fa69849f8127a325f9a9001284cd1bd3a59c:tests/phase_8_30_scope_migration.py", "4c903ac9aa43293c9f66b422bb0d49fd38dd8b49", "23d5b1a0a9e4f83ffd870f6b72693bb8878c85f94d8d7c142ca2a57fa0aeb218"),
    ("4110fa69849f8127a325f9a9001284cd1bd3a59c:tests/phase_8_37_scope_migration.py", "c5804e6d8d95a46792196cbedf42d1e469b85959", "79cbfffb932aea28321f017b76d26185774747a3d30cc0a7455530b6d01188cd"),
    ("4110fa69849f8127a325f9a9001284cd1bd3a59c:tests/phase8_byok_scope_migration.py", "191cc40fc191ce0c473d1e593e486cd8749bedf5", "d9d2dcaaa238b09013065c01bbe0228c850af05047c7381759b9869908ec9ac4"),
    ("4110fa69849f8127a325f9a9001284cd1bd3a59c:tests/test_first_run_connection_effect_isolation.py", "0d5d677327736595aed91a5bcb32d1e86e32ed47", "1dc16125889467087fd0372fd8d3ec4e304ba8a5aa34bf844bed26c5aed665f4"),
    ("4110fa69849f8127a325f9a9001284cd1bd3a59c:tests/test_first_run_connection_owner.py", "b690b808834bbe9cdbd7e24a4ad44f10252c37b2", "8dcead976d8b0e7f9a43ba955e6b69544a117d0d721ed7314f5823deb8dcf667"),
    ("4110fa69849f8127a325f9a9001284cd1bd3a59c:tests/test_phase_836_scope_integrity.py", "08699f706931595eb4384bc30bb30ab86aa81dcf", "2b7f0d1a14a57455ffd06e051e5ac076b4f2361902119fe58834f3a85fc7577b"),
    ("4110fa69849f8127a325f9a9001284cd1bd3a59c:tests/test_phase_837_scope_integrity.py", "b78421d6d478598821fd1be2554a3aa70fd3f918", "1110bcc403b96a47f6d29c4445a6e6419b69fd4f21c931bbd25ecb5ed415f2d8"),
    ("4110fa69849f8127a325f9a9001284cd1bd3a59c:tests/test_phase8_byok_scope_integrity.py", "f220cb4f0b6a09bf9c0f907ac2730a4dbfca7219", "2a6f888cd7a1059c0870a604541f9259d32243b37afea9038309f505b396e8e5"),
    # phase8_byok_b_scope_migration -- 23 entries
    ("e3612279cb972e68e2487702183d5bf5b8f6c4a1:.codex/CURRENT_STATE.md", "d7134c7d36a528bd3ed28c26ab55380874ce049c", "ecb30dd2d59a33cc34ea79b0c9f5350fe10c2bb4e43cac2b3d07e8dad3cdba65"),
    ("e3612279cb972e68e2487702183d5bf5b8f6c4a1:docs/phase8_first_run_connection_ui_design.md", "23cb60cefb9bc3b84bfb8a1f36257b6b946781fc", "04b37aee29abbfb350e80ccec65458556adaa4e1d3b3878d50597105a5098327"),
    ("e3612279cb972e68e2487702183d5bf5b8f6c4a1:nayeon/brain/onboarding_coordination.py", "b97e9d710bfd9cc7a31d8ec97525b9449700c228", "af479aa7597e036b84a5f21644182ea3bae2ba584d4c310c070aafb70ffddf15"),
    ("e3612279cb972e68e2487702183d5bf5b8f6c4a1:nayeon/brain/onboarding_recovery.py", "952eff66c91723a54086b41f8e5d384b8af5d593", "dbb2963de50326422c08ce0d46fec5920b6548d1210e0772429ea36c6d4a0738"),
    ("e3612279cb972e68e2487702183d5bf5b8f6c4a1:nayeon/desktop_alpha/application.py", "0062db49ce2be95c8359427707c91c741658354c", "af9bb617b67e56d2a71ae796af0f0846670303d0e192187a0ed6706127f73a82"),
    ("e3612279cb972e68e2487702183d5bf5b8f6c4a1:nayeon/desktop_alpha/first_run_connection_owner.py", "3273ce4c1681936ce7ae9a5e90d99a565acf6a82", "d3fb11f2c0095bb4e98d2a5339bb04f1ba73b286159083d32e6ccd07c2ee3e04"),
    ("e3612279cb972e68e2487702183d5bf5b8f6c4a1:nayeon/desktop_alpha/first_run_connection_window.py", "3e092bfe7651947a13583b8bfbef7b3a9ef5364d", "865fa15854591f151b2a6c17ef392636a0ea9950441c531b463c931e72bc1b32"),
    ("e3612279cb972e68e2487702183d5bf5b8f6c4a1:nayeon/desktop_alpha/workspace_window.py", "3aa881499d017b23cd55dd77e5e26c3638105365", "b7e78df7b0a786c0b4c5b19ec3a91f003f0995e496069e718c7389ff5871111c"),
    ("e3612279cb972e68e2487702183d5bf5b8f6c4a1:tests/phase_8_30_scope_migration.py", "6bc8987ff889d62e5675e937c489fdc63add8a97", "7fab9ace158264bdbf1c40838218576314649249ae8c89ecb5b52522c81562f3"),
    ("e3612279cb972e68e2487702183d5bf5b8f6c4a1:tests/phase_8_37_scope_migration.py", "3da61b15c74375775ca35605aed812c3b8c9e8da", "3f0ef3592754734e1050e5ce57aef50ce48de4b768019d72f6590ea3f73ddcaa"),
    ("e3612279cb972e68e2487702183d5bf5b8f6c4a1:tests/phase8_byok_b_scope_migration.py", "78733fe16623be018161e272286cf06afe820484", "7aa013c3400b4032087ad6f769d5ce0cb727d628586bb4f4cc4fdbca5c6f246c"),
    ("e3612279cb972e68e2487702183d5bf5b8f6c4a1:tests/phase8_byok_scope_migration.py", "f4d9f4f136afe09a622e1c2c0904c65f8790f06b", "7eaa989e141e17c7303ede283b3a979dc77680fa5b74d86a75dc8233ea4324b1"),
    ("e3612279cb972e68e2487702183d5bf5b8f6c4a1:tests/test_first_run_connection_application.py", "43066f07b2c5d19b667b3118890ee96454858795", "3c32da2c334dbda0acfe6911aee200d27648d4d71fb08ba5c665acfac11d2849"),
    ("e3612279cb972e68e2487702183d5bf5b8f6c4a1:tests/test_first_run_connection_cancelled_effect.py", "e6c111ee6c7184941e52d71535a590464e965d84", "26aa5cd65647316e9878b3ac2a0f89e739823923bee20cc0c9a0ce54c02c375a"),
    ("e3612279cb972e68e2487702183d5bf5b8f6c4a1:tests/test_first_run_connection_effect_isolation.py", "3ce94f67395f3370da412a85985b7a9b93c03dcc", "26b78138366ee6ec4cb8115c36e03d4dfa90a541ff5b9b3505a7f59c244cada7"),
    ("e3612279cb972e68e2487702183d5bf5b8f6c4a1:tests/test_first_run_connection_window.py", "fafa0f58c1d51fb3bffc067e59747de3af8cba91", "5c1fce9f76ba1d255ba3f4432da9ccef5edeb16717d3bf3709f512c3a8554757"),
    ("e3612279cb972e68e2487702183d5bf5b8f6c4a1:tests/test_phase_832_scope_integrity.py", "755c4c1f72f66cfd93b43bc41ca5e1c9f8f31eb9", "cc3d83397be376cce1fd1a005483e6576dea111da276a048685caf787d4058c8"),
    ("e3612279cb972e68e2487702183d5bf5b8f6c4a1:tests/test_phase_833_scope_integrity.py", "fe57747bb9bfda87d2bba4814ab29875d58be537", "4bdcd395b00a4d4e3ffd104ff17cc923f75075c20e457a090c045754700b5590"),
    ("e3612279cb972e68e2487702183d5bf5b8f6c4a1:tests/test_phase_834_scope_integrity.py", "373b5bd37faa6cc61c9211fc82e77ca34c41fa56", "142d05496a0a0d75a9d5a078b9e5144b4ab56821fd329b126903bd80e1a0e754"),
    ("e3612279cb972e68e2487702183d5bf5b8f6c4a1:tests/test_phase_836_scope_integrity.py", "1e00e9befc55ed68637dbf5bf6b0ef3954a1831f", "6ecb8d3ac9e970ef42d12855f81f406961cb82fcd71ef8bc26ed7e10ca822b8a"),
    ("e3612279cb972e68e2487702183d5bf5b8f6c4a1:tests/test_phase_837_scope_integrity.py", "78de2d5eb51d7640168be88b92112ed84662032c", "827678f7e01e8fe92b56045189fa7f97e363987b688c638bfcedb1abd99767e7"),
    ("e3612279cb972e68e2487702183d5bf5b8f6c4a1:tests/test_phase8_byok_b_scope_integrity.py", "6091cd5b37118bdf451deccbe1575e6c4dc824b0", "149cdf40c30ef4183ae41e6775d3a1950e09bb47d849eae1e90fa5b8b80e784a"),
    ("e3612279cb972e68e2487702183d5bf5b8f6c4a1:tests/test_phase8_byok_scope_integrity.py", "f8fc35f81f901bf10e0d7a916473769b6ffc8c1a", "5c369d3a04e5254b2205049b44ea3ef661ff32870d20ce14d8f26cf2ca143cc3"),
)

import argparse
import ast
import hashlib
import json
import math
import os
from pathlib import Path
import queue
import re
import subprocess
import sys
import tempfile
import threading
import time
import types
from types import MappingProxyType
import unittest
from unittest import mock
import uuid

PARENT = "f4e352b25d4654ad46e3b56bf40d8be01b7c56d6"
SOURCE = "096048db17c7c1f9402dfd16a7deb31e9ebdc81d"
BRANCH = "byok-c1-p243-g1-full-history-immutable-20261115"
TEST = "tests.test_phase8_byok_b_scope_integrity.ExactBYOKBTests.test_every_candidate_source_byte_is_bound"
ADDITIONS = (
    "scripts/p243_g1_older_seal_batch.py",
    "scripts/p243_g1_older_seal_batch_selftest.py",
    ".github/workflows/p243-g1-older-seal-batch.yml",
    "docs/byok-c1-p243-older-seal-batch.md",
)
DEPENDENCIES = {
    "p240_g1_safe_transport": "794d8b6c80e44a5da379359d3dbaa6ce96d21ae96b0f97ba11949759ee4515f3",
    "p239_g1_progress_observer": "9189fa9def1208039dce1a09c48265973eaf0b0e25d242b91a15ce74ab0c398f",
    "p238_g1_immutable_batch_candidate": "9f481c75764415fb4f829b3229d4989daf574b01ea7aa82241747a7cf4ff0eb7",
    "p234_windows_finegrain_diagnostic": "e4cdde2bbcd60ba54fd57cebfd335adcb5e13b6d72de1a6fb844574de4c6604c",
    "p240_g1_safe_transport_selftest": "dd011d785e317b1397423743ba209f97487931d81942d3c02192b9413ade6002",
    "p239_g1_progress_selftest": "cecc8481d25745731eb2eff4fe44b3164737be9afc20e595ffa8c60ae8080a6b",
    "p238_g1_batch_selftest": "72cdd09425960287bd38c8f79f2034b003d04a13c4a9eb4c61eef92a2b6e483c",
}
SOURCE_PINS = {
    "phase_8_30_scope_migration": "f9aa8c8df0144c83baa4edc8cc8d5f99ce5221c8c1263b13378feaeb87060487",
    "phase_8_31_scope_migration": "f1a0772533803b69719ad5af1d8ad1f84946b194259e682cbf809bcff83a5c99",
    "phase_8_32_scope_migration": "d658f8442c97225ac9ed1ddef187e25a6d423e6b2eeda3fcd6771fe47e11be02",
    "phase_8_33_scope_migration": "9af98a6fd435fea19f30ce00d03fb4f47a23ca64e9278fd9b4e06daaf53872bd",
    "phase_8_34_scope_migration": "59442121254b42949640161fb7dbd47e90f3e77e6045f258a1da130b640c8d43",
    "phase_8_36_scope_migration": "d63b58a03a00f573c6474a514f4f4e545b4a5ea3c85478fd824e1276862413e6",
    "phase_8_37_scope_migration": "3f0ef3592754734e1050e5ce57aef50ce48de4b768019d72f6590ea3f73ddcaa",
    "phase8_byok_scope_migration": "7eaa989e141e17c7303ede283b3a979dc77680fa5b74d86a75dc8233ea4324b1",
    "phase8_byok_b_scope_migration": "84ced2f31f5daf985de462c384abdfe47f8b705425f8bdefb8cf1e04e56ee010",
    "phase10_perception_scope_migration": "6999b151dcf634ed589df6b774b5a84c4252e77f38975f4f87af1a5b56efc9f0",
    "test_phase8_byok_b_scope_integrity": "65dad89298a587d6bb5dde5455df4d701bb1a1fd9a7a96cecf3e647800e3ae8b",
}
# Commit and table relationships follow the original callers inspected at P233.
# The third item names the function's original CRLF normalization at that call.
SPECS = (
    ("6030f9b7afacd0543912bfb4a8b4fe610ebd9632", "phase_8_30_scope_migration", "normal", ("APPROVED_NEW_SHA256", "APPROVED_MODIFIED_SHA256"), 5),
    ("79f17ca5211d7e1a97ef99b83dd613885d693bef", "phase_8_31_scope_migration", "normal", ("NEW", "MODIFIED"), 3),
    ("03f247d8627bf1c51105f73b9de5c6bbdf389cf9", "phase_8_32_scope_migration", "normal_self", ("CANDIDATE_SHA256",), 14),
    ("1a972d1d292597239c938d53437218c536b5bf3f", "phase_8_33_scope_migration", "self", ("CANDIDATE_SHA256",), 16),
    ("b0490cd9e72104a74a32dc5315cbc55bc4034676", "phase_8_34_scope_migration", "self", ("CANDIDATE_SHA256",), 20),
    ("a12565b9be070684e1d7d801ded4833d13121f94", "phase_8_36_scope_migration", "self", ("CANDIDATE_SHA256",), 19),
    ("87208af710bac90c440f2e0851854318b22e9b88", "phase_8_37_scope_migration", "self", ("CANDIDATE_SHA256",), 20),
    ("4110fa69849f8127a325f9a9001284cd1bd3a59c", "phase8_byok_scope_migration", "self", ("CANDIDATE_SHA256",), 11),
    ("e3612279cb972e68e2487702183d5bf5b8f6c4a1", "phase8_byok_b_scope_migration", "self", ("CANDIDATE_SHA256",), 23),
)
SECONDS = 180
READ_SECONDS = 20
MAX_READS = 16384
SAMPLE = 32
MAX_EVENTS = 4096
MAX_PROGRESS = 2 * 1024 * 1024
MAX_LINE = 2048
MAX_COUNTER = 1_000_000
STAGES = ("child_started", "source_verified", "baseline_verified",
          "preflight_complete", "test_begun", "running", "test_finished",
          "postflight_complete")
COUNTERS = ("validated_reads", "delegated_started", "delegated_completed",
            "delegated_show_completed", "delegated_cat_file_completed",
            "delegated_ls_tree_completed", "delegated_other_completed",
            "subtests_completed", "subtests_failed")
KEYS = {"schema", "binding", "seq", "stage", "seconds", *COUNTERS}
NATIVE = subprocess.check_output


def require(ok, code):
    if not ok:
        raise RuntimeError(code)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load_dependencies(root):
    """Authenticate every dependency before executing any of those bytes."""
    raws = {}
    for name, pin in DEPENDENCIES.items():
        path = root / "scripts" / (name + ".py")
        raw = path.read_bytes()
        require(len(raw) <= 4 * 1024 * 1024 and sha(raw) == pin, "DEPENDENCY_PIN")
        raws[name] = raw
    modules = {}
    for name in tuple(DEPENDENCIES)[:4]:
        path = root / "scripts" / (name + ".py")
        module = types.ModuleType("p243_authenticated_" + name)
        module.__file__ = str(path)
        exec(compile(raws[name], str(path), "exec"), module.__dict__)
        modules[name] = module
    return modules


def binding(run_id):
    require(type(run_id) is str and re.fullmatch(r"[0-9a-f]{32}", run_id), "RUN_ID")
    return sha((run_id + SOURCE + PARENT + DEPENDENCIES[
        "p239_g1_progress_observer"]).encode("ascii"))


# P239 progress copied with schema/binding and finite read cap updated only.
def zeros():
    return dict.fromkeys(COUNTERS, 0)


def unique_object(pairs):
    obj = {}
    for key, value in pairs:
        require(key not in obj, "DUPLICATE_KEY")
        obj[key] = value
    return obj


def validate_event(event, previous, expected_binding):
    require(type(event) is dict and set(event) == KEYS, "EVENT_SCHEMA")
    require(type(event["schema"]) is int and event["schema"] == 243
            and event["binding"] == expected_binding, "FOREIGN_EVENT")
    require(type(event["seq"]) is int and event["seq"] == (
        previous["seq"] + 1 if previous else 1), "EVENT_SEQUENCE")
    seconds = event["seconds"]
    require(type(seconds) in (int, float) and 0 <= seconds <= SECONDS
            and math.isfinite(seconds), "EVENT_CLOCK")
    stage = event["stage"]
    require(type(stage) is str and stage in STAGES, "EVENT_STAGE")
    for key in COUNTERS:
        value = event[key]
        require(type(value) is int and 0 <= value <= MAX_COUNTER, "COUNTER_CAP")
        require(previous is None or value >= previous[key], "COUNTER_REGRESSION")
    require(event["validated_reads"] <= MAX_READS
            and event["subtests_failed"] <= event["subtests_completed"] <= 23
            and event["delegated_completed"] <= event["delegated_started"]
            and sum(event[k] for k in COUNTERS[3:7]) == event["delegated_completed"],
            "COUNTER_RELATION")
    if previous is None:
        require(stage == STAGES[0] and all(event[k] == 0 for k in COUNTERS), "MISSING_START")
    else:
        old = previous["stage"]
        transitions = {
            "child_started": {"source_verified"},
            "source_verified": {"baseline_verified"},
            "baseline_verified": {"preflight_complete"},
            "preflight_complete": {"test_begun"},
            "test_begun": {"running", "test_finished"},
            "running": {"running", "test_finished"},
            "test_finished": {"postflight_complete"},
            "postflight_complete": set(),
        }
        require(stage in transitions[old], "STAGE_ORDER")
        require(seconds >= previous["seconds"], "CLOCK_REGRESSION")
        require(stage != "running" or any(event[k] != previous[k] for k in COUNTERS),
                "DUPLICATE_SAMPLE")
        require(event["subtests_completed"] - previous["subtests_completed"] in (0, 1)
                and 0 <= event["subtests_failed"] - previous["subtests_failed"]
                <= event["subtests_completed"] - previous["subtests_completed"],
                "SUBTEST_SEQUENCE")
        require(stage == "running" or event["subtests_completed"] == previous["subtests_completed"],
                "SUBTEST_STAGE")
        require(old != "test_finished" or all(event[k] == previous[k] for k in COUNTERS),
                "POSTFLIGHT_COUNTS")
    require(STAGES.index(stage) >= STAGES.index("test_begun")
            or event["subtests_completed"] == event["validated_reads"] == 0,
            "PREMATURE_COUNTS")
    require(stage not in STAGES[:3] or all(event[k] == 0 for k in COUNTERS), "PREFLIGHT_COUNTS")


def parse_progress(raw, run_id):
    """Read-only prefix parser. Last timestamp is a sample, NEVER a duration.

    Torn/invalid/foreign evidence cannot be complete. Safe prefix counters are
    lower bounds only; they never establish test success or source authority.
    """
    report = {"raw_sha256": sha(raw), "raw_bytes": len(raw), "accepted_events": 0,
              "records_valid": False, "observation_complete": False,
              "reason": "MISSING", "latest_stage": None,
              "latest_sample_seconds": None, "safe_counts": zeros(),
              "stage_first_seconds": dict.fromkeys(STAGES, None)}
    if not raw:
        return report
    if len(raw) > MAX_PROGRESS:
        report["reason"] = "BYTE_CAP"
        return report
    previous = None
    expected = binding(run_id)
    lines = raw.split(b"\n")
    try:
        for line in lines[:-1]:
            require(report["accepted_events"] < MAX_EVENTS, "EVENT_CAP")
            require(0 < len(line) <= MAX_LINE, "LINE_CAP")
            event = json.loads(line, object_pairs_hook=unique_object)
            validate_event(event, previous, expected)
            previous = event
            report.update(accepted_events=event["seq"], latest_stage=event["stage"],
                          latest_sample_seconds=event["seconds"],
                          safe_counts={k: event[k] for k in COUNTERS})
            if report["stage_first_seconds"][event["stage"]] is None:
                report["stage_first_seconds"][event["stage"]] = event["seconds"]
        require(not lines[-1], "TORN_TRAILING_LINE")
        require(previous is not None, "MISSING")
        report.update(records_valid=True, reason="VALID_PREFIX",
                      observation_complete=previous["stage"] == "postflight_complete")
    except (RuntimeError, ValueError, UnicodeError, RecursionError) as error:
        # JSON parser messages can contain raw data: export fixed codes only.
        report["reason"] = (str(error) if type(error) is RuntimeError else "INVALID_JSON")
    return report


class Progress:
    """One exclusive append-only file; <=4096 lines, <=2 MiB, flush each line."""
    def __init__(self, path, run_id, origin):
        self.stream = path.open("xb", buffering=0)
        self.binding, self.origin = binding(run_id), origin
        self.counts, self.previous, self.size = zeros(), None, 0
        self.reads_by_path = {}
        self.active = False

    def emit(self, stage):
        event = dict(self.counts, schema=243, binding=self.binding,
                     seq=self.previous["seq"] + 1 if self.previous else 1,
                     stage=stage, seconds=round(time.monotonic() - self.origin, 6))
        validate_event(event, self.previous, self.binding)
        raw = json.dumps(event, sort_keys=True, allow_nan=False).encode("ascii") + b"\n"
        require(event["seq"] <= MAX_EVENTS and len(raw) - 1 <= MAX_LINE
                and self.size + len(raw) <= MAX_PROGRESS, "PROGRESS_CAP")
        require(self.stream.write(raw) == len(raw), "PROGRESS_SHORT_WRITE")
        self.stream.flush()
        self.previous, self.size = event, self.size + len(raw)

    def sample(self, counter):
        if self.active and self.counts[counter] % SAMPLE == 0:
            self.emit("running")

    def subtest(self, err):
        require(self.active, "SUBTEST_OUTSIDE_TEST")
        self.counts["subtests_completed"] += 1
        self.counts["subtests_failed"] += int(err is not None)
        self.emit("running")

    def close(self):
        self.stream.close()


class JournalMirror:
    """Observe original start/stop only AFTER its private journal is flushed."""
    def __init__(self, stream, progress, test_id):
        self.stream, self.progress, self.test_id = stream, progress, test_id
        self.pending = None

    def write(self, raw):
        require(self.pending is None, "JOURNAL_PENDING")
        event = json.loads(raw)
        require(set(event) == {"event", "id"} and event["id"] == self.test_id
                and event["event"] in {"start", "stop"}, "JOURNAL_EVENT")
        result = self.stream.write(raw)
        self.pending = event["event"]
        return result

    def flush(self):
        self.stream.flush()
        if self.pending is not None:
            stage = "test_begun" if self.pending == "start" else "test_finished"
            self.progress.emit(stage)
            self.progress.active = self.pending == "start"
            self.pending = None


def result_class(original, progress):
    class InstrumentedJournalResult(original.JournalResult):
        def addSubTest(self, test, subtest, err):
            super().addSubTest(test, subtest, err)
            progress.subtest(err)  # Completion observation only, no outcome change.
    return InstrumentedJournalResult


def delegated_kind(args):
    # Inspect only for aggregate fixed counters. Never serialize argv or paths.
    if (args and type(args[0]) is list and len(args[0]) >= 2
            and type(args[0][0]) is str and args[0][0] == "git"
            and type(args[0][1]) is str):
        return {"show": "show", "cat-file": "cat_file", "ls-tree": "ls_tree"}.get(
            args[0][1], "other")
    return "other"  # includes any unmatched check_output call; no inferred Git identity


# P239 supervisor copied verbatim. __file__ selects this P243 child.
def contained(source, private, run_id, helper, seconds=SECONDS, job_factory=None):
    """P238 supervisor semantics, separate P239 child; no budget extension."""
    require(type(seconds) is int and seconds == SECONDS, "ORIGINAL_BUDGET")
    binding(run_id)
    record = {"timed_out": False, "tree_cleanup": "UNCERTAIN", "aborted": False,
              "residual_descendants_after_root_exit": False,
              "configured_whole_child_seconds": SECONDS, "actual_process_exit": None}
    proc = None
    job = (job_factory or helper.Job)()
    began = time.monotonic()
    command = [sys.executable, "-B", str(Path(__file__).resolve()), "_child",
               "--source", str(source), "--output", str(private), "--run-id", run_id,
               "--origin", repr(began)]
    try:
        with (private / "candidate.log").open("wb") as sink:
            proc = subprocess.Popen(command, cwd=source, env=helper.environment(),
                                    stdin=subprocess.PIPE, stdout=sink, stderr=subprocess.STDOUT)
            job.assign(proc)
            require(job.active() == 1, "JOB_HANDSHAKE")
            proc.stdin.write(b"!")
            proc.stdin.close()
            while proc.poll() is None:
                if time.monotonic() - began >= seconds:
                    record["timed_out"] = True
                    break
                require((private / "candidate.log").stat().st_size <= helper.MAX_LOG, "LOG_CAP")
                time.sleep(0.1)
    except Exception:
        record["aborted"] = True
    finally:
        try:
            active = job.active()
            if active and proc is not None and proc.poll() is not None and not record["timed_out"]:
                record["residual_descendants_after_root_exit"] = True
            if active:
                job.terminate()
            end = time.monotonic() + 5
            while job.active() and time.monotonic() < end:
                time.sleep(0.05)
            if job.active() == 0:
                record["tree_cleanup"] = "JOB_EMPTY_CONFIRMED"
            if proc is not None:
                if proc.poll() is None:
                    proc.kill()
                proc.wait(timeout=5)
                record["actual_process_exit"] = proc.returncode
        except Exception:
            record["tree_cleanup"] = "UNCERTAIN"
        finally:
            try:
                job.close()
            except Exception:
                record["tree_cleanup"] = "UNCERTAIN"
            if proc is not None and record["actual_process_exit"] is None:
                try:
                    if proc.poll() is None:
                        proc.kill()
                    proc.wait(timeout=5)
                    record["actual_process_exit"] = proc.returncode
                except Exception:
                    record["tree_cleanup"] = "UNCERTAIN"
        record["elapsed_seconds_including_cleanup"] = round(time.monotonic() - began, 3)
    return record


def assignments(raw):
    result = {}
    for node in ast.parse(raw).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name):
                require(target.id not in result, "DUPLICATE_SOURCE_ASSIGNMENT")
                result[target.id] = node.value
    return result


def literal(name, values, old=None):
    """Evaluate the exact original literal syntax with two bounded references."""
    def value(node):
        if isinstance(node, ast.Name):
            require(node.id in values, "UNKNOWN_LITERAL_NAME")
            return value(values[node.id])
        if isinstance(node, ast.Attribute):
            require(isinstance(node.value, ast.Name) and node.value.id == "old"
                    and old is not None and node.attr in old, "UNKNOWN_OLD_LITERAL")
            return ast.literal_eval(old[node.attr])
        if isinstance(node, ast.Dict):
            pairs = [(value(k), value(v)) for k, v in zip(node.keys, node.values)]
            require(len(dict(pairs)) == len(pairs), "DUPLICATE_LITERAL_PATH")
            return dict(pairs)
        if isinstance(node, ast.Tuple):
            return tuple(value(n) for n in node.elts)
        require(isinstance(node, ast.Constant), "NONLITERAL_SOURCE_PIN")
        return ast.literal_eval(node)
    require(name in values, "MISSING_LITERAL")
    return value(values[name])


def original_function(raw, name, namespace, with_self=False):
    """Compile only the pinned original normalizer, with private frozen globals."""
    nodes = ast.parse(raw).body
    selected = []
    if with_self:
        selected = [n for n in nodes if isinstance(n, ast.Assign)
                    and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name)
                    and n.targets[0].id in {"SELF", "SELF_PIN"}]
        require(len(selected) == 2, "SELF_DEFINITION")
    functions = [n for n in nodes if isinstance(n, ast.FunctionDef) and n.name == name]
    require(len(functions) == 1, "ORIGINAL_NORMALIZER_DEFINITION")
    scope = dict(namespace, hashlib=hashlib, re=re)
    exec(compile(ast.Module(body=selected + functions, type_ignores=[]),
                 "<p243-authenticated-normalizer>", "exec"), scope)
    return scope[name]


def derive_sources(raws):
    """No imports, live pin dictionaries, refs or newly computed success pins."""
    require(set(raws) == set(SOURCE_PINS), "SOURCE_SET")
    for name, raw in raws.items():
        require(type(raw) is bytes and sha(raw) == SOURCE_PINS[name], "ORIGINAL_SOURCE_PIN")
    values = {name: assignments(raw) for name, raw in raws.items()}
    normal = original_function(raws["phase_8_30_scope_migration"], "_normal", {})
    old_sha = original_function(raws["phase_8_31_scope_migration"], "_sha",
                                {"prior": types.SimpleNamespace(_normal=normal)})
    manifest, digests = {}, {}
    for commit, name, rule, tables, count in SPECS:
        source_pins = {}
        for table in tables:
            pins = literal(table, values[name])
            require(type(pins) is dict and not set(pins) & set(source_pins), "PIN_TABLE_OVERLAP")
            source_pins.update(pins)
        require(len(source_pins) == count, "FINITE_SOURCE_COUNT")
        rows = {query: (oid, pin) for query, oid, pin in ROWS
                if query.startswith(commit + ":")}
        require(len(rows) == count and {q.split(":", 1)[1]: p for q, (_, p) in rows.items()}
                == source_pins, "LITERAL_MANIFEST_EQUALITY")
        if rule == "normal":
            def digest(path, raw, frozen_sha=old_sha):
                return frozen_sha(raw)
        else:
            frozen_digest = original_function(raws[name], "_digest", {}, with_self=True)
            if rule == "normal_self":
                def digest(path, raw, frozen=frozen_digest, normalize=normal):
                    return frozen(path, normalize(raw))
            else:
                digest = frozen_digest
        digests[commit] = digest
        for query, (oid, pin) in rows.items():
            require(re.fullmatch(r"[0-9a-f]{40}", oid)
                    and re.fullmatch(r"[0-9a-f]{64}", pin) and pin != "0" * 64,
                    "MANIFEST_IDENTITY")
            manifest[query] = (oid, pin)
    require(len(ROWS) == len(manifest) == 131, "FINITE_MANIFEST")
    return MappingProxyType(manifest), MappingProxyType(digests), values


def object_oid(kind, raw):
    return hashlib.sha1(kind.encode("ascii") + b" " + str(len(raw)).encode("ascii")
                        + b"\0" + raw).hexdigest()


def authenticate_seals(root, values, helper):
    seals = literal("SEALS", values["phase_8_32_scope_migration"],
                    values["phase_8_31_scope_migration"])
    expected_trees = {}
    for name, prefix in (
            ("phase_8_33_scope_migration", "PROTECTED"),
            ("phase_8_34_scope_migration", "PROTECTED"),
            ("phase_8_36_scope_migration", "PROTECTED"),
            ("phase_8_37_scope_migration", "PROTECTED"),
            ("phase8_byok_scope_migration", "PARENT"),
            ("phase8_byok_b_scope_migration", "PARENT"),
            ("phase10_perception_scope_migration", "PARENT")):
        constants = values[name]
        tag = literal(prefix + "_TAG", constants)
        obj = literal(prefix + "_TAG_OBJECT", constants)
        commit = literal(prefix, constants)
        require(tag not in seals, "DUPLICATE_SEAL")
        seals[tag] = (obj, commit)
        expected_trees[commit] = literal(prefix + "_TREE", constants)
    trees = {}
    for tag, (obj, commit) in seals.items():
        require(helper.git(root, "show-ref", "--verify", "--hash", "--",
                           "refs/tags/" + tag) == (obj + "\n").encode(), "SEAL_REF")
        require(helper.git(root, "cat-file", "-t", obj) == b"tag\n"
                and helper.git(root, "cat-file", "-t", commit) == b"commit\n", "SEAL_TYPES")
        raw_tag = helper.git(root, "cat-file", "tag", obj)
        require(object_oid("tag", raw_tag) == obj and raw_tag.split(b"\n")[:3] == [
            ("object " + commit).encode(), b"type commit", ("tag " + tag).encode()], "RAW_TAG")
        require(helper.git(root, "rev-parse", "--verify", "--end-of-options", obj + "^{}")
                == (commit + "\n").encode(), "SEAL_PEEL")
        raw_commit = helper.git(root, "cat-file", "commit", commit)
        require(object_oid("commit", raw_commit) == commit, "RAW_COMMIT")
        first = raw_commit.split(b"\n", 1)[0]
        require(re.fullmatch(rb"tree [0-9a-f]{40}", first), "COMMIT_TREE")
        tree = first[5:].decode("ascii")
        require(commit not in expected_trees or tree == expected_trees[commit], "LITERAL_TREE")
        require(helper.git(root, "rev-parse", commit + "^{tree}") == (tree + "\n").encode()
                and helper.git(root, "cat-file", "-t", tree) == b"tree\n", "TREE_TYPE")
        raw_tree = helper.git(root, "cat-file", "tree", tree)
        require(object_oid("tree", raw_tree) == tree, "RAW_TREE")
        trees[commit] = helper.git(root, "ls-tree", "-r", "-z", "--full-tree", commit)
    require({s[0] for s in SPECS} <= set(trees), "MISSING_MANIFEST_SEAL")
    return trees


def verify_frame(query, header, raw, delimiter, manifest, witnesses, digests, helper):
    require(query in manifest, "UNADMITTED_QUERY")
    oid, pin = manifest[query]
    match = helper.HEADER.fullmatch(header) if type(header) is bytes else None
    require(match is not None and match[1].decode("ascii") == oid, "HEADER_IDENTITY")
    require(type(raw) is bytes and len(raw) == int(match[2]) <= helper.MAX_BLOB
            and delimiter == b"\n", "FRAME")
    require(helper.blob(raw) == oid, "BLOB_IDENTITY")
    commit, path = query.split(":", 1)
    require(digests[commit](path, raw) == pin, "ORIGINAL_NORMALIZED_PIN")
    require(query in witnesses and raw == witnesses[query], "ORIGINAL_SHOW_BYTES")
    return raw


def preflight(source, helper):
    raws = {}
    for name in SOURCE_PINS:
        path = "tests/" + name + ".py"
        raw = helper.git(source, "show", SOURCE + ":" + path)
        require(helper.read(source / path) == raw, "SOURCE_DISK_WITNESS")
        raws[name] = raw
    manifest, digests, values = derive_sources(raws)
    trees = authenticate_seals(source, values, helper)
    # P238's 23 entries must remain exactly the same immutable B requests.
    b = SPECS[-1][0]
    require({q[len(b) + 1:]: v for q, v in manifest.items() if q.startswith(b + ":")}
            == helper.MANIFEST, "P238_EXACT_23")
    witnesses = {}
    for query, (oid, _) in manifest.items():
        commit, path = query.split(":", 1)
        row = ("100644 blob " + oid + "\t" + path).encode("utf8")
        require(trees[commit].split(b"\0").count(row) == 1, "EXACT_TREE_PATH_OID")
        # This is the exact native signature later eligible for interception.
        raw = NATIVE(["git", "show", query], cwd=source,
                     stderr=subprocess.DEVNULL, timeout=20)
        verify_frame(query, f"{oid} blob {len(raw)}\n".encode("ascii"), raw, b"\n",
                     manifest, {query: raw}, digests, helper)
        witnesses[query] = raw
    return manifest, MappingProxyType(witnesses), digests


def intercept_query(args, kwargs, root, manifest):
    if (len(args) != 1 or type(args[0]) is not list or len(args[0]) != 3
            or any(type(x) is not str for x in args[0]) or args[0][:2] != ["git", "show"]
            or set(kwargs) != {"cwd", "stderr", "timeout"}
            or type(kwargs["cwd"]) is not type(root) or kwargs["cwd"] != root
            or type(kwargs["stderr"]) is not int or kwargs["stderr"] != subprocess.DEVNULL
            or type(kwargs["timeout"]) is not int or kwargs["timeout"] != READ_SECONDS):
        return None
    query = args[0][2]
    return query if query in manifest else None


class Batch:
    """Fresh bounded exchanges only. No retry, fallback or shared result cache."""
    def __init__(self, root, manifest, witnesses, digests, helper):
        self.manifest, self.witnesses, self.digests = manifest, witnesses, digests
        self.helper = helper
        self.sequence, self.poisoned = 0, False
        self.lock = threading.Lock()
        self.proc = subprocess.Popen(["git", "cat-file", "--batch"], cwd=root,
                                     env=helper.environment(), stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=0)

    def get(self, query):
        acquired = self.lock.acquire(blocking=False)
        if not acquired:
            self.poisoned = True
            raise RuntimeError("CONCURRENT_BATCH_CALL")
        try:
            require(not self.poisoned and query in self.manifest
                    and self.sequence < MAX_READS, "BATCH_STATE")
            self.sequence += 1
            ticket = self.sequence
            reply = queue.Queue(maxsize=1)

            def exchange():
                try:
                    require(self.proc.poll() is None, "BATCH_EXIT")
                    request = (self.manifest[query][0] + "\n").encode("ascii")
                    require(self.proc.stdin.write(request) == len(request), "SHORT_WRITE")
                    self.proc.stdin.flush()
                    reply.put((ticket, self.helper.frame(self.proc.stdout)))
                except Exception:
                    reply.put((ticket, None))

            threading.Thread(target=exchange, daemon=True).start()
            frame = self.helper.accept_reply(ticket, reply.get(timeout=READ_SECONDS))
            raw = verify_frame(query, *frame, self.manifest, self.witnesses, self.digests, self.helper)
            require(not self.poisoned, "POISONED_DURING_READ")
            return raw
        except Exception:
            self.poisoned = True
            raise
        finally:
            self.lock.release()

    def close(self):
        # The pinned P238 cleanup uses only proc/poisoned and retains its bounds.
        self.helper.Batch.close(self)


def transport(root, manifest, batch, native, progress):
    def limited(*args, **kwargs):
        query = intercept_query(args, kwargs, root, manifest)
        # A native mock/wrapper supplied as the delegate keeps full native mock
        # semantics. Wrappers above this function see and transform its reply.
        if query is not None and native is NATIVE:
            raw = batch.get(query)
            progress.counts["validated_reads"] += 1
            progress.reads_by_path[query] = progress.reads_by_path.get(query, 0) + 1
            progress.sample("validated_reads")
            return raw
        progress.counts["delegated_started"] += 1
        kind = delegated_kind(args)
        try:
            raw = native(*args, **kwargs)
        except BaseException:
            # Preserve the exact native exception even if progress sampling
            # would itself refuse a malformed or exhausted evidence stream.
            progress.counts["delegated_completed"] += 1
            progress.counts["delegated_" + kind + "_completed"] += 1
            raise
        progress.counts["delegated_completed"] += 1
        progress.counts["delegated_" + kind + "_completed"] += 1
        progress.sample("delegated_completed")
        return raw
    return limited


def check_delta(parents, rows):
    require(parents == [PARENT], "EXACT_PARENT")
    require(sorted(rows) == sorted("A\t" + p for p in ADDITIONS), "EXACT_ADDITIONS")


def provenance(root, helper):
    require(sys.platform == "win32" and os.getenv("GITHUB_ACTIONS") == "true"
            and os.getenv("RUNNER_OS") == "Windows"
            and os.getenv("RUNNER_ENVIRONMENT") == "github-hosted"
            and os.getenv("GITHUB_REPOSITORY") == "krismcan/Mark-LV"
            and os.getenv("GITHUB_EVENT_NAME") == "push"
            and os.getenv("GITHUB_REF_NAME") == BRANCH, "HOST_IDENTITY")
    git = lambda *args: helper.git(root, *args)
    head = git("rev-parse", "HEAD").decode().strip()
    require(head == os.getenv("GITHUB_SHA"), "CONTROLLER_HEAD")
    require(git("rev-parse", "--is-shallow-repository") == b"false\n", "FULL_HISTORY")
    require(git("rev-parse", "--show-object-format") == b"sha1\n", "OBJECT_FORMAT")
    require(git("config", "--get", "core.autocrlf").strip() == b"false", "RAW_LF_CHECKOUT")
    require(not git("status", "--porcelain=v1", "-uall", "--ignored=matching"), "DIRTY")
    require(not git("for-each-ref", "refs/replace"), "REPLACEMENT_OBJECTS")
    common = Path(git("rev-parse", "--git-common-dir").decode().strip())
    if not common.is_absolute():
        common = root / common
    require(not (common / "info/grafts").exists()
            and not (common / "objects/info/alternates").exists(), "GRAFT_OR_ALTERNATES")
    check_delta(git("rev-list", "--parents", "-n", "1", head).decode().split()[1:],
                git("diff-tree", "--no-commit-id", "--name-status", "-r", "--no-renames",
                    PARENT, head).decode().splitlines())
    hashes = []
    for path in ADDITIONS:
        raw = helper.read(root / path)
        require(b"\r" not in raw and raw.endswith(b"\n"), "ADDITION_LF")
        row = git("ls-tree", head, "--", path)
        require(row == ("100644 blob " + helper.blob(raw) + "\t" + path + "\n").encode(),
                "ADDITION_MODE_OID")
        require(raw == git("show", head + ":" + path), "ADDITION_DISK")
        hashes.append(sha(raw))
    for name, pin in DEPENDENCIES.items():
        path = "scripts/" + name + ".py"
        raw = helper.read(root / path)
        require(sha(raw) == pin and raw == git("show", head + ":" + path)
                and raw == git("show", PARENT + ":" + path), "DEPENDENCY_BYTES")
    return {"head": head, "parent": PARENT, "additions_sha256_in_fixed_order": hashes,
            "dependency_sha256_in_fixed_order": list(DEPENDENCIES.values())}


def private_paths(source, output, root):
    runner_temp = Path(os.environ["RUNNER_TEMP"]).resolve(strict=True)
    require(output.is_relative_to(runner_temp) and output != runner_temp
            and not output.is_relative_to(root) and not output.is_relative_to(source)
            and not root.is_relative_to(source) and not source.is_relative_to(root), "PATH_SEPARATION")
    return runner_temp


def child(source, private, run_id, origin, modules):
    require(sys.stdin.buffer.read(1) == b"!", "SUPERVISOR_HANDSHAKE")
    root = Path(__file__).resolve().parents[1]
    private_paths(source, private, root)
    helper = modules["p238_g1_immutable_batch_candidate"]
    equality = modules["p240_g1_safe_transport"]
    original = modules["p234_windows_finegrain_diagnostic"]
    require(math.isfinite(origin) and origin <= time.monotonic(), "CLOCK_ORIGIN")
    provenance(root, helper)
    progress = Progress(private / "progress.jsonl", run_id, origin)
    try:
        progress.emit("child_started")
        before_raw = original.canonical(original.verify_source(source))
        before_sha = sha(before_raw)
        (private / "source-before.json").write_bytes(before_raw)
        progress.emit("source_verified")
        manifest, witnesses, digests = preflight(source, helper)
        progress.emit("baseline_verified")
        sys.path.insert(0, str(source))
        batch = Batch(source, manifest, witnesses, digests, helper)
        result = None
        try:
            with mock.patch.object(subprocess, "check_output", transport(
                    source, manifest, batch, NATIVE, progress)):
                loader = unittest.TestLoader()
                suite = loader.loadTestsFromName(TEST)
                require(not loader.errors and suite.countTestCases() == 1, "ONE_G1_ONLY")
                progress.emit("preflight_complete")
                with (private / "events.jsonl").open("x", encoding="utf8") as stream:
                    cls = result_class(original, progress)
                    cls.journal = JournalMirror(stream, progress, TEST)
                    result = unittest.TextTestRunner(verbosity=2, resultclass=cls).run(suite)
        finally:
            if result is not None:
                code = 0 if result.wasSuccessful() else 1
                helper.write(private / "result.json", {
                    "assigned": [TEST], "tests_run": result.testsRun, "original_unittest_exit": code,
                    "failures": [t.id() for t, _ in result.failures],
                    "errors": [t.id() for t, _ in result.errors],
                    "skips": [t.id() for t, _ in result.skipped],
                    "expected_failures": [t.id() for t in result.expectedFailures],
                    "unexpected_successes": [t.id() for t in result.unexpectedSuccesses]})
            try:
                batch.close()
            finally:
                helper.write(private / "metrics.json", {
                    "counts": progress.counts, "reads_by_query": progress.reads_by_path,
                    "manifest_entries": len(manifest), "preflight_native_show_calls": len(witnesses),
                    "manifest_sha256": sha(original.canonical(ROWS)),
                    "show_witnesses_sha256": sha(original.canonical(
                        {q: sha(raw) for q, raw in witnesses.items()}))})
        equality.revalidate_source(original, source, before_raw, before_sha)
        helper.write(private / "verified.json", {"canonical_bytes_equal": True,
                                                "before_sha256": before_sha})
        progress.emit("postflight_complete")
        return code
    finally:
        progress.close()


def execute(mode, source, output, modules):
    root = Path(__file__).resolve().parents[1]
    source, output = source.resolve(strict=True), output.resolve()
    runner_temp = private_paths(source, output, root)
    output.mkdir(exist_ok=True)
    report = {"schema": 243, "scope": "INSTRUMENTED CANDIDATE", "release": "HOLD",
              "source": SOURCE, "mode": mode, "exit": 125, "g1_executed": False,
              "test_body_unchanged": True, "full_unfiltered_regressions": "0/3",
              "qualified_approvals": "0/7", "SEC03_SEC04": "OPEN", "real_key": "NO-GO"}
    private = None
    helper = modules["p238_g1_immutable_batch_candidate"]
    original = modules["p234_windows_finegrain_diagnostic"]
    equality = modules["p240_g1_safe_transport"]
    observer = modules["p239_g1_progress_observer"]
    try:
        controller = provenance(root, helper)
        report["controller"] = controller
        before_raw = original.canonical(original.verify_source(source))
        before_sha = sha(before_raw)
        report["source_before_sha256"] = before_sha
        if mode == "guard":
            report["exit"] = 0
        else:
            require(mode == "observe", "MODE")
            private = Path(tempfile.mkdtemp(prefix="p243-private-", dir=runner_temp)).resolve()
            private_paths(source, private, root)
            require(not output.is_relative_to(private), "PRIVATE_SEPARATION")
            run_id = uuid.uuid4().hex
            process = contained(source, private, run_id, helper)
            report["process"] = process
            progress_raw = helper.read(private / "progress.jsonl", MAX_PROGRESS) if (
                private / "progress.jsonl").exists() else b""
            witness = parse_progress(progress_raw, run_id)
            report["progress"] = witness
            result = json.loads(helper.read(private / "result.json")) if (
                private / "result.json").exists() else None
            events = [json.loads(line) for line in helper.read(private / "events.jsonl").splitlines()] if (
                private / "events.jsonl").exists() else []
            report["g1_executed"] = any(e.get("event") == "start" for e in events)
            if result is not None:
                report["recorded_candidate_unittest_exit"] = result["original_unittest_exit"]
            summary, code = helper.classify(process, result, events, original)
            report.update(candidate_result=summary, classifier_exit=code)
            equal = False
            if process["tree_cleanup"] == "JOB_EMPTY_CONFIRMED":
                equality.revalidate_source(original, source, before_raw, before_sha)
                if (private / "source-before.json").exists():
                    require(helper.read(private / "source-before.json") == before_raw, "CHILD_BEFORE_BYTES")
                    equal = True
            report["source_canonical_bytes_equal"] = equal
            report["exit"] = observer.evidence_exit(code, witness, equal)
            if code == 3:
                verified = json.loads(helper.read(private / "verified.json"))
                require(verified == {"canonical_bytes_equal": True, "before_sha256": before_sha},
                        "CHILD_POSTFLIGHT")
                metrics = json.loads(helper.read(private / "metrics.json"))
                reads = metrics["reads_by_query"]
                require(set(reads) == {r[0] for r in ROWS}
                        and all(type(n) is int and n > 0 for n in reads.values())
                        and sum(reads.values()) == witness["safe_counts"]["validated_reads"]
                        and metrics["counts"] == witness["safe_counts"], "EXACT_131_COVERAGE")
                report["metrics"] = {k: v for k, v in metrics.items() if k != "reads_by_query"}
                report["older_seal_reads"] = sum(n for q, n in reads.items()
                                                  if not q.startswith(SPECS[-1][0] + ":"))
        require(provenance(root, helper) == controller, "CONTROLLER_CHANGED")
    except Exception:
        report.update(exit=1 if report.get("classifier_exit") == 1 else 125,
                      error="SOURCE_CONTAINMENT_INSTRUMENTATION_OR_RESULT_REFUSED")
    finally:
        if private is not None:
            receipts = {}
            for name in ("candidate.log", "progress.jsonl", "events.jsonl", "result.json",
                         "source-before.json", "verified.json", "metrics.json"):
                try:
                    if (private / name).exists():
                        receipts[name] = sha(helper.read(private / name))
                except Exception:
                    receipts[name] = "UNAVAILABLE_OR_OVERSIZED"
            report["raw_private_sha256"] = receipts
        helper.write(output / (mode + ".json"), report)
        print("P243_EXIT=" + str(report["exit"]) + "|ALL_C1_GATES_HOLD")
    return report["exit"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("guard", "observe", "_child"))
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-id")
    parser.add_argument("--origin", type=float)
    args = parser.parse_args()
    modules = load_dependencies(Path(__file__).resolve().parents[1])
    if args.mode == "_child":
        require(type(args.origin) is float and math.isfinite(args.origin), "CLOCK_ORIGIN")
        return child(args.source.resolve(strict=True), args.output.resolve(strict=True),
                     args.run_id, args.origin, modules)
    return execute(args.mode, args.source, args.output, modules)


if __name__ == "__main__":
    raise SystemExit(main())
